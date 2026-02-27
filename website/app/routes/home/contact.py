from flask import render_template, request, redirect, url_for, flash, current_app
from flask_mail import Message
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app import db, mail
from app.models.models import ContactMessage
from . import home_bp

@home_bp.route('/contact')
def contact():
    return render_template('/home/contact.html')

@home_bp.route('/es/contact')
def contact_es():
    return render_template('/home/es/contact.html')


@home_bp.route('/contact/submit', methods=['POST'])
def submit_contact_message():
    name = request.form.get('name', '').strip()
    email = request.form.get('_replyto', '').strip()
    message = request.form.get('message', '').strip()
    locale = request.form.get('locale', 'en').strip().lower()

    if locale not in {'en', 'es'}:
        locale = 'en'

    redirect_endpoint = 'home.contact_es' if locale == 'es' else 'home.contact'
    success_message = '¡Gracias! Tu mensaje fue enviado correctamente.' if locale == 'es' else 'Thank you! Your message was sent successfully.'
    error_message = 'Hubo un problema al enviar tu mensaje. Revisa los datos e inténtalo de nuevo.' if locale == 'es' else 'There was a problem sending your message. Please check your information and try again.'

    if not name or not email or not message:
        flash(error_message, 'error')
        return redirect(url_for(redirect_endpoint))

    if len(name) > 100 or len(email) > 120 or len(message) > 1000:
        flash(error_message, 'error')
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

        confirmation_html = render_template(
            'emails/email_response_template.html',
            title=confirmation_title,
            description=confirmation_description,
            year=current_year,
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