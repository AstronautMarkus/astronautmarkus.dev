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


def verify_turnstile_token(token, remote_ip=None):
    secret_key = (current_app.config.get('TURNSTILE_SECRET_KEY') or '').strip()
    if not secret_key:
        current_app.logger.warning('Turnstile verification skipped: TURNSTILE_SECRET_KEY is not configured')
        return False

    payload = {
        'secret': secret_key,
        'response': token,
    }
    if remote_ip:
        payload['remoteip'] = remote_ip

    data = urlparse.urlencode(payload).encode('utf-8')
    verification_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    http_request = urlrequest.Request(verification_url, data=data, method='POST')
    http_request.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urlrequest.urlopen(http_request, timeout=8) as response:
            verification_result = json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, TimeoutError, ValueError):
        current_app.logger.exception('Turnstile verification failed')
        return False

    return bool(verification_result.get('success'))

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
        contact_message = ContactMessage(name=name, email=email, message=message)
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