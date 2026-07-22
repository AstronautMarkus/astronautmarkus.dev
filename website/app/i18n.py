from flask import g, current_app, render_template
from jinja2 import TemplateNotFound

SUPPORTED_LANGUAGES = ('en', 'es')
LANG_COOKIE_NAME    = 'lang'
DEFAULT_LANGUAGE    = 'en'


def get_current_language():
    """Return the active language for the current request, falling back to the default."""
    lang = getattr(g, 'current_lang', None)
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


def localized_template_name(template_name: str) -> str:
    """
    Given a template path, return the localized variant if it exists.

    Examples (lang = 'es'):
        'home.html'              -> 'home_es.html'        (if it exists)
        'emails/contact.html'    -> 'emails/contact_es.html'  (if it exists)
        'home.html'              -> 'home.html'           (fallback when _es missing)
    """
    lang = get_current_language()

    if lang == DEFAULT_LANGUAGE:
        return template_name

    dot = template_name.rfind('.')
    candidate = (
        f'{template_name}_{lang}'
        if dot == -1
        else f'{template_name[:dot]}_{lang}{template_name[dot:]}'
    )

    try:
        current_app.jinja_loader.get_source(current_app.jinja_env, candidate)
        return candidate
    except TemplateNotFound:
        return template_name


def render_localized_template(template_name: str, **context):
    """Drop-in replacement for render_template that auto-selects the localized variant."""
    return render_template(localized_template_name(template_name), **context)
