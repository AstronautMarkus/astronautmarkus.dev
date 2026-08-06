from datetime import datetime, timedelta

from flask import current_app, url_for
from flask_mail import Message
from jinja2 import Environment, select_autoescape

from app import db, mail
from app.models.models import HoneypotHit, MailTemplate, User

_DEFAULT_TEMPLATE = {
    'slug': 'honeypot_alert',
    'language': 'es',
    'description': 'Correo enviado a los administradores cuando el honeypot captura un nuevo atacante',
    'subject': '[Honeypot] Actividad detectada: {{ resource }}',
    'body_html': (
        '<p>El honeypot <strong>kanarianlintu</strong> registró una nueva solicitud.</p>'
        '<table cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-family:monospace">'
        '<tr><td style="font-weight:bold;padding-right:12px">IP</td><td>{{ ip_address }}</td></tr>'
        '<tr><td style="font-weight:bold;padding-right:12px">Recurso</td><td>{{ resource }}</td></tr>'
        '<tr><td style="font-weight:bold;padding-right:12px">Ruta</td><td>{{ method }} {{ path }}</td></tr>'
        '<tr><td style="font-weight:bold;padding-right:12px">User-Agent</td><td>{{ user_agent }}</td></tr>'
        '<tr><td style="font-weight:bold;padding-right:12px">Referrer</td><td>{{ referrer }}</td></tr>'
        '<tr><td style="font-weight:bold;padding-right:12px">Fecha</td><td>{{ created_at }}</td></tr>'
        '</table>'
        '<p><a href="{{ detail_url }}">Ver detalle completo →</a></p>'
    ),
}


def _seed_template() -> MailTemplate:
    tpl = MailTemplate.query.filter_by(slug='honeypot_alert', language='es').first()
    if not tpl:
        tpl = MailTemplate(**_DEFAULT_TEMPLATE)
        db.session.add(tpl)
        db.session.commit()
    return tpl


def _render(text: str, **kwargs) -> str:
    env = Environment(autoescape=select_autoescape(['html']))
    return env.from_string(text).render(**kwargs)


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
        tpl = _seed_template()
        context = {
            'ip_address': hit.ip_address,
            'resource': hit.resource or hit.path,
            'method': hit.method,
            'path': hit.path,
            'user_agent': hit.user_agent or '—',
            'referrer': hit.referrer or '—',
            'created_at': hit.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if hit.created_at else '',
            'detail_url': url_for('admin.honeypot_detail', hit_id=hit.id, _external=True),
        }
        subject = _render(tpl.subject, **context)
        body = _render(tpl.body_html, **context)
        msg = Message(subject=subject, recipients=recipients, html=body)
        mail.send(msg)
    except Exception as exc:
        current_app.logger.error('Honeypot alert mail error: %s', exc)
