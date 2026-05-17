import re

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_mail import Message
from jinja2 import Environment, select_autoescape

from app import db, mail
from app.i18n import get_current_language, render_localized_template
from app.models.models import ContactMessage, MailTemplate
from app.routes.contact import contact_bp

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# ─── Default templates ────────────────────────────────────────────────────────

_DEFAULT_TEMPLATES = [
    {
        'slug': 'contact_notification',
        'language': 'en',
        'description': 'Email sent to you when someone fills the contact form (English)',
        'subject': 'New message: {{ subject }}',
        'body_html': (
            '<p>You received a new contact message from your website.</p>'
            '<table cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-family:monospace">'
            '<tr><td style="font-weight:bold;padding-right:12px">From</td><td>{{ name }} &lt;{{ email }}&gt;</td></tr>'
            '<tr><td style="font-weight:bold;padding-right:12px">Subject</td><td>{{ subject }}</td></tr>'
            '<tr><td style="font-weight:bold;padding-right:12px;vertical-align:top">Message</td>'
            '<td style="white-space:pre-wrap">{{ message }}</td></tr>'
            '</table>'
        ),
    },
    {
        'slug': 'contact_notification',
        'language': 'es',
        'description': 'Correo enviado a ti cuando alguien completa el formulario de contacto (Español)',
        'subject': 'Nuevo mensaje: {{ subject }}',
        'body_html': (
            '<p>Recibiste un nuevo mensaje de contacto desde tu sitio web.</p>'
            '<table cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-family:monospace">'
            '<tr><td style="font-weight:bold;padding-right:12px">De</td><td>{{ name }} &lt;{{ email }}&gt;</td></tr>'
            '<tr><td style="font-weight:bold;padding-right:12px">Asunto</td><td>{{ subject }}</td></tr>'
            '<tr><td style="font-weight:bold;padding-right:12px;vertical-align:top">Mensaje</td>'
            '<td style="white-space:pre-wrap">{{ message }}</td></tr>'
            '</table>'
        ),
    },
    {
        'slug': 'contact_autoresponse',
        'language': 'en',
        'description': 'Autoresponse sent to the person who submitted the form (English)',
        'subject': 'Thanks for reaching out, {{ name }}!',
        'body_html': (
            '<p>Hi {{ name }},</p>'
            "<p>Thanks for your message! I've received it and will get back to you as soon as possible.</p>"
            '<p>Here is a copy of what you sent:</p>'
            '<blockquote style="border-left:3px solid #ccc;margin:0;padding:0 12px;color:#555">'
            '<strong>Subject:</strong> {{ subject }}<br><br>'
            '{{ message }}'
            '</blockquote>'
            '<p>Best regards,<br>Marcos — AstronautMarkus.dev</p>'
        ),
    },
    {
        'slug': 'contact_autoresponse',
        'language': 'es',
        'description': 'Respuesta automática enviada a quien completó el formulario (Español)',
        'subject': '¡Gracias por escribirme, {{ name }}!',
        'body_html': (
            '<p>Hola {{ name }},</p>'
            '<p>¡Gracias por tu mensaje! Lo he recibido y te responderé lo antes posible.</p>'
            '<p>Aquí tienes una copia de lo que enviaste:</p>'
            '<blockquote style="border-left:3px solid #ccc;margin:0;padding:0 12px;color:#555">'
            '<strong>Asunto:</strong> {{ subject }}<br><br>'
            '{{ message }}'
            '</blockquote>'
            '<p>Un saludo,<br>Marcos — AstronautMarkus.dev</p>'
        ),
    },
]


def _seed_templates() -> None:
    """Insert default mail templates if they don't exist yet."""
    for tpl in _DEFAULT_TEMPLATES:
        exists = MailTemplate.query.filter_by(
            slug=tpl['slug'], language=tpl['language']
        ).first()
        if not exists:
            db.session.add(MailTemplate(**tpl))
    db.session.commit()


def _render_body(body_html: str, **kwargs) -> str:
    env = Environment(autoescape=select_autoescape(['html']))
    return env.from_string(body_html).render(**kwargs)


def _get_template(slug: str, lang: str) -> MailTemplate | None:
    return MailTemplate.query.filter_by(slug=slug, language=lang).first()


def _send_notification(lang: str, name: str, email: str, subject: str, message: str) -> None:
    tpl = _get_template('contact_notification', lang) or _get_template('contact_notification', 'en')
    if not tpl:
        return
    rendered_subject = _render_body(tpl.subject, name=name, email=email, subject=subject, message=message)
    rendered_body = _render_body(tpl.body_html, name=name, email=email, subject=subject, message=message)
    admin_email = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
    msg = Message(
        subject=rendered_subject,
        recipients=[admin_email],
        html=rendered_body,
        reply_to=email,
    )
    mail.send(msg)


def _send_autoresponse(lang: str, name: str, email: str, subject: str, message: str) -> None:
    tpl = _get_template('contact_autoresponse', lang) or _get_template('contact_autoresponse', 'en')
    if not tpl:
        return
    rendered_subject = _render_body(tpl.subject, name=name, email=email, subject=subject, message=message)
    rendered_body = _render_body(tpl.body_html, name=name, email=email, subject=subject, message=message)
    msg = Message(
        subject=rendered_subject,
        recipients=[email],
        html=rendered_body,
    )
    mail.send(msg)


# ─── Route ────────────────────────────────────────────────────────────────────

@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    lang = get_current_language()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

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
                form_data={'name': name, 'email': email, 'subject': subject, 'message': message},
            )

        # Persist
        entry = ContactMessage(name=name, email=email, subject=subject, message=message, language=lang)
        db.session.add(entry)
        db.session.commit()

        # Send emails (non-fatal)
        try:
            _seed_templates()
            _send_notification(lang, name, email, subject, message)
            _send_autoresponse(lang, name, email, subject, message)
        except Exception as exc:
            current_app.logger.error('Contact mail error: %s', exc)

        flash('sent', 'success')
        return redirect(url_for('contact.contact'))

    return render_localized_template('main/contact.html', field_errors=[], form_data={})
