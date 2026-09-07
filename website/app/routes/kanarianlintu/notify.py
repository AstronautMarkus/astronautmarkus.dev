from datetime import datetime, timedelta

from flask import current_app, url_for
from flask_mail import Message

from app import mail
from app.emails import render_email
from app.models.models import HoneypotHit, User


def _should_alert(hit: HoneypotHit) -> bool:
    """Throttle alerts per-IP so a single scan burst doesn't flood the inbox."""
    cooldown = current_app.config.get('HONEYPOT_ALERT_COOLDOWN_MINUTES', 60)
    window_start = datetime.utcnow() - timedelta(minutes=cooldown)
    recent = (
        HoneypotHit.query
        .filter(
            HoneypotHit.ip_address == hit.ip_address,
            HoneypotHit.id != hit.id,
            HoneypotHit.created_at >= window_start,
        )
        .first()
    )
    return recent is None


def notify_admins(hit: HoneypotHit) -> None:
    """Email every registered admin user when a new attacker is caught, throttled per-IP."""
    if not _should_alert(hit):
        return

    recipients = [email for (email,) in User.query.with_entities(User.email).all() if email]
    if not recipients:
        return

    try:
        resource = hit.resource or hit.path
        context = {
            'ip_address': hit.ip_address,
            'resource': resource,
            'method': hit.method,
            'path': hit.path,
            'user_agent': hit.user_agent or '—',
            'referrer': hit.referrer or '—',
            'created_at': hit.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if hit.created_at else '',
            'detail_url': url_for('admin.honeypot_detail', hit_id=hit.id, _external=True),
        }
        subject = f'[Honeypot] Actividad detectada: {resource}'
        body = render_email('emails/honeypot_alert.html', **context)
        msg = Message(subject=subject, recipients=recipients, html=body)
        mail.send(msg)
    except Exception as exc:
        current_app.logger.error('Honeypot alert mail error: %s', exc)
