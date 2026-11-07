import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_mail import Message

from app import db, mail
from app.emails import render_email, template_for
from app.i18n import get_current_language, render_localized_template
from app.models.models import BlockedSender, ContactMessage, ContactSubmissionLog
from app.routes.contact import contact_bp

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# ─── Anti-spam ─────────────────────────────────────────────────────────────────

HONEYPOT_FIELD = 'company_site'  # decoy field — real users never see or fill it
MIN_SUBMIT_SECONDS = 3           # forms submitted faster than this are treated as bots
RATE_LIMIT_WINDOW_MINUTES = 10
RATE_LIMIT_MAX_ATTEMPTS = 3      # attempts allowed per email/IP within the window before auto-ban

# ─── Mail subjects ─────────────────────────────────────────────────────────────

_SUBJECTS = {
    'contact_notification': {
        'en': 'New message: {subject}',
        'es': 'Nuevo mensaje: {subject}',
    },
    'contact_autoresponse': {
        'en': 'Thanks for reaching out, {name}!',
        'es': '¡Gracias por escribirme, {name}!',
    },
}


def _subject(key: str, lang: str, **kwargs) -> str:
    return _SUBJECTS[key].get(lang, _SUBJECTS[key]['en']).format(**kwargs)


_PRIVATE_IP_PREFIXES = ('127.', '::1', '10.', '172.', '192.168.', '::ffff:127.')


def _verify_turnstile(token: str, remote_ip: str | None = None) -> bool:
    """Verify a Cloudflare Turnstile token. Returns True if valid or if not configured."""
    secret = current_app.config.get('TURNSTILE_SECRET_KEY', '')
    if not secret:
        return True
    if not token:
        current_app.logger.warning('Turnstile: empty token received')
        return False
    data: dict = {'secret': secret, 'response': token}
    # remoteip is optional; omit loopback/private addresses to avoid rejection
    if remote_ip and not any(remote_ip.startswith(p) for p in _PRIVATE_IP_PREFIXES):
        data['remoteip'] = remote_ip
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        data=payload,
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            result = json.loads(resp.read().decode())
            success = bool(result.get('success', False))
            if not success:
                current_app.logger.warning(
                    'Turnstile verification failed — error-codes: %s',
                    result.get('error-codes', []),
                )
            return success
    except Exception as exc:
        current_app.logger.error('Turnstile verification error: %s', exc)
        return False


def _send_notification(lang: str, name: str, email: str, subject: str, message: str) -> None:
    admin_email = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
    rendered_subject = _subject('contact_notification', lang, subject=subject)
    rendered_body = render_email(
        template_for('emails/contact_notification', lang),
        name=name, email=email, subject=subject, message=message,
    )
    msg = Message(
        subject=rendered_subject,
        recipients=[admin_email],
        html=rendered_body,
        reply_to=email,
    )
    mail.send(msg)


def _send_autoresponse(lang: str, name: str, email: str, subject: str, message: str) -> None:
    rendered_subject = _subject('contact_autoresponse', lang, name=name)
    rendered_body = render_email(
        template_for('emails/contact_autoresponse', lang),
        name=name, email=email, subject=subject, message=message,
    )
    msg = Message(
        subject=rendered_subject,
        recipients=[email],
        html=rendered_body,
    )
    mail.send(msg)


def _is_blocked(email: str, ip: str | None) -> bool:
    conditions = [BlockedSender.email == email] if email else []
    if ip:
        conditions.append(BlockedSender.ip_address == ip)
    if not conditions:
        return False
    return BlockedSender.query.filter(db.or_(*conditions)).first() is not None


def _check_rate_limit_and_maybe_ban(email: str, ip: str | None) -> bool:
    """Log this attempt and ban the sender if they've exceeded the rate limit. Returns True if banned."""
    # created_at is populated via the DB server's NOW(), so the window must use the same clock (not UTC).
    window_start = datetime.now() - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
    conditions = [ContactSubmissionLog.email == email]
    if ip:
        conditions.append(ContactSubmissionLog.ip_address == ip)
    recent_attempts = ContactSubmissionLog.query.filter(
        ContactSubmissionLog.created_at >= window_start,
        db.or_(*conditions),
    ).count()

    db.session.add(ContactSubmissionLog(email=email, ip_address=ip))

    if recent_attempts >= RATE_LIMIT_MAX_ATTEMPTS:
        db.session.add(BlockedSender(email=email, ip_address=ip, reason='rate_limit_exceeded'))
        db.session.commit()
        current_app.logger.warning('Contact form: auto-banned email=%s ip=%s (rate limit)', email, ip)
        return True

    db.session.commit()
    return False


# ─── Route ────────────────────────────────────────────────────────────────────

@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    lang = get_current_language()
    turnstile_site_key = current_app.config.get('TURNSTILE_SITE_KEY', '')

    if not current_app.config.get('CONTACT_FORM_ENABLED', True):
        return render_localized_template(
            'main/contact.html',
            field_errors=[],
            form_data={},
            turnstile_site_key=turnstile_site_key,
            turnstile_error=False,
            form_disabled=True,
            form_ts=time.time(),
        )

    if request.method == 'POST':
        ip = request.remote_addr
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        form_data = {'name': name, 'email': email, 'subject': subject, 'message': message}

        # Honeypot — a hidden field real visitors never fill. Pretend success so bots don't adapt.
        if request.form.get(HONEYPOT_FIELD, '').strip():
            current_app.logger.warning('Contact form: honeypot triggered from ip=%s', ip)
            flash('sent', 'success')
            return redirect(url_for('contact.contact'))

        # Timing trap — forms submitted faster than a human can fill are almost certainly scripted.
        try:
            rendered_at = float(request.form.get('form_ts', ''))
        except ValueError:
            rendered_at = 0.0
        if rendered_at and (time.time() - rendered_at) < MIN_SUBMIT_SECONDS:
            current_app.logger.warning('Contact form: submitted too fast from ip=%s', ip)
            flash('sent', 'success')
            return redirect(url_for('contact.contact'))

        # Already-banned senders are dropped silently, before any validation/API calls.
        if _is_blocked(email, ip):
            flash('sent', 'success')
            return redirect(url_for('contact.contact'))

        field_errors: list[str] = []
        if not name:
            field_errors.append('name')
        if not email or not _EMAIL_RE.match(email):
            field_errors.append('email')
        if not subject:
            field_errors.append('subject')
        if not message:
            field_errors.append('message')

        if field_errors:
            flash('validation_error', 'error')
            return render_localized_template(
                'main/contact.html',
                field_errors=field_errors,
                form_data=form_data,
                turnstile_site_key=turnstile_site_key,
                turnstile_error=False,
                form_ts=time.time(),
            )

        turnstile_token = request.form.get('cf-turnstile-response', '')
        if not _verify_turnstile(turnstile_token, ip):
            return render_localized_template(
                'main/contact.html',
                field_errors=[],
                form_data=form_data,
                turnstile_site_key=turnstile_site_key,
                turnstile_error=True,
                form_ts=time.time(),
            )

        # Rate limit — too many attempts from this email/IP in the window bans them going forward.
        if _check_rate_limit_and_maybe_ban(email, ip):
            flash('sent', 'success')
            return redirect(url_for('contact.contact'))

        # Persist
        entry = ContactMessage(name=name, email=email, subject=subject, message=message, language=lang)
        db.session.add(entry)
        db.session.commit()

        # Send emails (non-fatal)
        try:
            _send_notification(lang, name, email, subject, message)
            _send_autoresponse(lang, name, email, subject, message)
        except Exception as exc:
            current_app.logger.error('Contact mail error: %s', exc)

        flash('sent', 'success')
        return redirect(url_for('contact.contact'))

    return render_localized_template(
        'main/contact.html',
        field_errors=[],
        form_data={},
        turnstile_site_key=turnstile_site_key,
        turnstile_error=False,
        form_ts=time.time(),
    )
