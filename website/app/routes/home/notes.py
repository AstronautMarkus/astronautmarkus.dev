import random
import json
from urllib import parse as urlparse, request as urlrequest
from urllib.error import HTTPError, URLError
from flask import render_template, request, redirect, url_for, flash, current_app
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models.models import Note
from . import home_bp

NOTE_COLORS = [
    'hotpink',
    'cyan',
    'lime',
    'gold',
    'orchid',
    'skyblue',
    'khaki',
    'plum',
    'lightcoral',
    'palegreen',
]

SMILLEYS = [
    'hi.gif',
    'hunter.gif',
    'jester.gif',
    'laugh3.gif',
    'lazy.gif',
    'music.gif',
    'negative.gif',
    'neo.gif',
    'paladin.gif',
    'read.gif',
    'sun_bespectacled.gif',
    'superman.gif',
    'yahoo.gif'
]


def _get_notes_messages(locale='en'):
    if locale == 'es':
        return {
            'empty_content': 'El contenido no puede estar vacío.',
            'long_content': 'El contenido debe tener máximo 100 caracteres.',
            'long_username': 'El nombre debe tener máximo 20 caracteres.',
            'missing_ip': 'No fue posible detectar tu IP. Intenta de nuevo.',
            'captcha_error': 'Completa la verificación de seguridad para continuar.',
            'success': 'Nota agregada correctamente.',
            'db_error': 'Ocurrió un error al guardar la nota. Intenta de nuevo.',
        }

    return {
        'empty_content': 'Note content cannot be empty.',
        'long_content': 'Note content must be 100 characters or less.',
        'long_username': 'Username must be 20 characters or less.',
        'missing_ip': 'Unable to detect your IP address. Please try again.',
        'captcha_error': 'Please complete the security verification to continue.',
        'success': 'Note added successfully!',
        'db_error': 'An error occurred while adding the note. Please try again.',
    }


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


def _is_anonymous_selected(username, anonymous_flag):
    normalized_name = (username or '').strip().lower()
    normalized_flag = (anonymous_flag or '').strip().lower()

    if normalized_name == 'anonymous':
        return True

    if normalized_flag in {'1', 'true', 'on', 'yes', 'anonymous'}:
        return True

    return not normalized_name


def _get_or_create_anonymous_username(ip_address):
    existing_note = (
        Note.query
        .filter(
            Note.ip_address == ip_address,
            Note.username.like('anonymous#%')
        )
        .order_by(Note.created_at.desc())
        .first()
    )

    if existing_note:
        return existing_note.username

    return f"anonymous#{random.randint(1000, 9999)}"


def _notes_handler(locale='en'):
    is_spanish = locale == 'es'
    messages = _get_notes_messages(locale)
    template_path = 'home/es/notes.html' if is_spanish else 'home/notes.html'
    redirect_endpoint = 'home.es_notes' if is_spanish else 'home.notes'
    turnstile_site_key = (current_app.config.get('TURNSTILE_SITE_KEY') or '').strip()

    if request.method == 'POST':
        content = (request.form.get('content') or '').strip()
        raw_username = request.form.get('username', '').strip()
        raw_anonymous_flag = request.form.get('anonymous', '')
        turnstile_token = request.form.get('cf-turnstile-response', '').strip()

        if not content:
            flash(messages['empty_content'], 'danger')
            return redirect(url_for(redirect_endpoint))

        if len(content) > 100:
            flash(messages['long_content'], 'danger')
            return redirect(url_for(redirect_endpoint))

        if len(raw_username) > 20:
            flash(messages['long_username'], 'danger')
            return redirect(url_for(redirect_endpoint))

        ip_address = request.remote_addr
        if not ip_address:
            flash(messages['missing_ip'], 'danger')
            return redirect(url_for(redirect_endpoint))

        if not turnstile_token or not verify_turnstile_token(turnstile_token, ip_address):
            flash(messages['captcha_error'], 'danger')
            return redirect(url_for(redirect_endpoint))

        is_anonymous = _is_anonymous_selected(raw_username, raw_anonymous_flag)

        if is_anonymous:
            username = _get_or_create_anonymous_username(ip_address)
        else:
            username = raw_username

        new_note = Note(
            content=content,
            username=username,
            color=random.choice(NOTE_COLORS),
            ip_address=ip_address,
            language=locale
        )

        try:
            db.session.add(new_note)
            db.session.commit()
            flash(messages['success'], 'success')
        except SQLAlchemyError as error:
            db.session.rollback()
            current_app.logger.error('Database error while saving note: %s', error)
            flash(messages['db_error'], 'danger')

        return redirect(url_for(redirect_endpoint))

    notes = (
        Note.query
        .filter_by(language=locale)
        .order_by(Note.created_at.desc())
        .all()
    )
    return render_template(
        template_path,
        notes=notes,
        smilleys=SMILLEYS,
        turnstile_site_key=turnstile_site_key,
    )

@home_bp.route('/notes', methods=['GET', 'POST'])
def notes():
    return _notes_handler(locale='en')

@home_bp.route('/es/notes', methods=['GET', 'POST'])
def es_notes():
    return _notes_handler(locale='es')
