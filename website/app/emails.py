from flask import render_template, url_for

APP_URL = 'https://astronautmarkus.dev'
APP_URL_DISPLAY = 'astronautmarkus.dev'


def template_for(base: str, lang: str) -> str:
    """Resolve a language-specific email template, e.g. ('emails/foo', 'es') -> 'emails/foo_es.html'."""
    return f'{base}_es.html' if lang == 'es' else f'{base}.html'


def render_email(template_name: str, **context) -> str:
    """Render an email HTML template with the shared banner/footer context."""
    context.setdefault('banner_url', url_for('static', filename='images/banner.png', _external=True))
    context.setdefault('app_url', APP_URL)
    context.setdefault('app_url_display', APP_URL_DISPLAY)
    return render_template(template_name, **context)
