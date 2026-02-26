from flask import render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.models import ContactMessage
from . import home_bp

@home_bp.route('/contact')
def contact():
    return render_template('contact.html')

@home_bp.route('/es/contact')
def contact_es():
    return render_template('/es/contact.html')


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

    flash(success_message, 'success')
    return redirect(url_for(redirect_endpoint))