from flask import render_template, request, redirect, url_for, flash, current_app
from flask_mail import Message
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from urllib import parse as urlparse, request as urlrequest
from urllib.error import HTTPError, URLError
import json
from app import db, mail
from app.models.models import ContactMessage
from . import home_bp


def _turnstile_verify_request(payload):
    data = urlparse.urlencode(payload).encode('utf-8')
    verification_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    http_request = urlrequest.Request(verification_url, data=data, method='POST')
    http_request.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urlrequest.urlopen(http_request, timeout=8) as response:
            return True, response.status, json.loads(response.read().decode('utf-8'))
    except HTTPError as error:
        error_body = ''
        try:
            error_body = error.read().decode('utf-8')
        except Exception:
            pass

        error_payload = {}
        if error_body:
            try:
                error_payload = json.loads(error_body)
            except ValueError:
                error_payload = {'raw': error_body}

        return False, error.code, error_payload
    except (URLError, TimeoutError, ValueError):
        current_app.logger.exception('Turnstile verification request failed')
        return False, None, {}


def verify_turnstile_token(token, remote_ip=None):
    secret_key = (current_app.config.get('TURNSTILE_SECRET_KEY') or '').strip()
    if not secret_key:
        current_app.logger.warning('Turnstile verification skipped: TURNSTILE_SECRET_KEY is not configured')
        return False

    if not token:
        return False

    if remote_ip and ',' in remote_ip:
        remote_ip = remote_ip.split(',', 1)[0].strip()

    payload = {
        'secret': secret_key,
        'response': token,
    }
    if remote_ip:
        payload['remoteip'] = remote_ip

    request_ok, status_code, verification_result = _turnstile_verify_request(payload)

    if not request_ok and status_code == 400 and 'remoteip' in payload:
        current_app.logger.warning('Turnstile returned HTTP 400 with remoteip, retrying without remoteip')
        payload.pop('remoteip', None)
        request_ok, status_code, verification_result = _turnstile_verify_request(payload)

    if not request_ok:
        error_codes = verification_result.get('error-codes') if isinstance(verification_result, dict) else None
        if isinstance(error_codes, list) and 'invalid-input-secret' in error_codes:
            current_app.logger.error(
                'Turnstile secret key is invalid. Verify TURNSTILE_SECRET_KEY (use Secret key, not Site key, for the same widget/environment).'
            )
        current_app.logger.warning('Turnstile verification failed with HTTP %s (error-codes=%s)', status_code, error_codes)
        return False

    is_success = bool(verification_result.get('success'))
    if not is_success:
        error_codes = verification_result.get('error-codes')
        current_app.logger.info('Turnstile token rejected (error-codes=%s)', error_codes)

    return is_success

@home_bp.route('/contact')
def contact():
    turnstile_site_key = (current_app.config.get('TURNSTILE_SITE_KEY') or '').strip()
    return render_template('/home/contact.html', turnstile_site_key=turnstile_site_key)

@home_bp.route('/es/contact')
def contact_es():
    turnstile_site_key = (current_app.config.get('TURNSTILE_SITE_KEY') or '').strip()
    return render_template('/home/es/contact.html', turnstile_site_key=turnstile_site_key)


@home_bp.route('/contact/submit', methods=['POST'])
def submit_contact_message():
    name = request.form.get('name', '').strip()
    email = request.form.get('_replyto', '').strip()
    message = request.form.get('message', '').strip()
    turnstile_token = request.form.get('cf-turnstile-response', '').strip()
    locale = request.form.get('locale', 'en').strip().lower()

    if locale not in {'en', 'es'}:
        locale = 'en'

    redirect_endpoint = 'home.contact_es' if locale == 'es' else 'home.contact'
    success_message = '¡Gracias! Tu mensaje fue enviado correctamente.' if locale == 'es' else 'Thank you! Your message was sent successfully.'
    error_message = 'Hubo un problema al enviar tu mensaje. Revisa los datos e inténtalo de nuevo.' if locale == 'es' else 'There was a problem sending your message. Please check your information and try again.'
    captcha_error_message = 'Completa la verificación de seguridad para continuar.' if locale == 'es' else 'Please complete the security verification to continue.'

    if not name or not email or not message:
        flash(error_message, 'error')
        return redirect(url_for(redirect_endpoint))

    if len(name) > 100 or len(email) > 120 or len(message) > 1000:
        flash(error_message, 'error')
        return redirect(url_for(redirect_endpoint))

    if not turnstile_token or not verify_turnstile_token(turnstile_token, request.remote_addr):
        flash(captcha_error_message, 'error')
        return redirect(url_for(redirect_endpoint))

    try:
        contact_message = ContactMessage(name=name, email=email, message=message, language=locale)
        db.session.add(contact_message)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        flash(error_message, 'error')
        return redirect(url_for(redirect_endpoint))

    mailbox = (current_app.config.get('MAIL_USERNAME') or '').strip()
    if not mailbox:
        current_app.logger.warning('Contact email skipped: MAIL_USERNAME is not configured')
        flash(error_message, 'error')
        return redirect(url_for(redirect_endpoint))

    subject = 'Nuevo mensaje de contacto' if locale == 'es' else 'New contact message'
    body = (
        f'Nombre: {name}\n'
        f'Email: {email}\n\n'
        f'Mensaje:\n{message}'
    )

    try:
        email_message = Message(
            subject=subject,
            sender=mailbox,
            recipients=[mailbox],
            body=body,
            reply_to=email,
        )
        mail.send(email_message)

        current_year = datetime.now().year
        confirmation_title = 'Mensaje recibido' if locale == 'es' else 'Message received'
        confirmation_description = (
            '¡Gracias por escribirme! Revisaré tu mensaje y te responderé pronto.'
            if locale == 'es'
            else 'Thanks for reaching out! I will review your message and get back to you soon.'
        )
        dont_respond = ('No respondas a este correo, es solo una confirmación automática. -AstroBot' 
            if locale == 'es' 
            else 'Do not reply to this email, it is just an automatic confirmation. -AstroBot')

        confirmation_html = render_template(
            'emails/email_response_template.html',
            title=confirmation_title,
            description=confirmation_description,
            year=current_year,
            dont_respond=dont_respond
        )

        user_subject = 'Confirmación de contacto' if locale == 'es' else 'Contact confirmation'
        user_email_message = Message(
            subject=user_subject,
            sender=mailbox,
            recipients=[email],
            html=confirmation_html,
        )
        mail.send(user_email_message)
    except Exception:
        current_app.logger.exception('Failed to send contact email')
        flash(error_message, 'error')
        return redirect(url_for(redirect_endpoint))

    flash(success_message, 'success')
    return redirect(url_for(redirect_endpoint))