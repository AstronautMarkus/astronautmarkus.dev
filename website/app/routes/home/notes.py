import random
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


def _get_notes_messages(locale='en'):
    if locale == 'es':
        return {
            'empty_content': 'El contenido no puede estar vacío.',
            'long_content': 'El contenido debe tener máximo 200 caracteres.',
            'long_username': 'El nombre debe tener máximo 20 caracteres.',
            'missing_ip': 'No fue posible detectar tu IP. Intenta de nuevo.',
            'success': 'Nota agregada correctamente.',
            'db_error': 'Ocurrió un error al guardar la nota. Intenta de nuevo.',
        }

    return {
        'empty_content': 'Note content cannot be empty.',
        'long_content': 'Note content must be 200 characters or less.',
        'long_username': 'Username must be 20 characters or less.',
        'missing_ip': 'Unable to detect your IP address. Please try again.',
        'success': 'Note added successfully!',
        'db_error': 'An error occurred while adding the note. Please try again.',
    }


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

    if request.method == 'POST':
        content = (request.form.get('content') or '').strip()
        raw_username = request.form.get('username', '').strip()
        raw_anonymous_flag = request.form.get('anonymous', '')

        if not content:
            flash(messages['empty_content'], 'danger')
            return redirect(url_for(redirect_endpoint))

        if len(content) > 200:
            flash(messages['long_content'], 'danger')
            return redirect(url_for(redirect_endpoint))

        if len(raw_username) > 20:
            flash(messages['long_username'], 'danger')
            return redirect(url_for(redirect_endpoint))

        ip_address = request.remote_addr
        if not ip_address:
            flash(messages['missing_ip'], 'danger')
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
    return render_template(template_path, notes=notes)

@home_bp.route('/notes', methods=['GET', 'POST'])
def notes():
    return _notes_handler(locale='en')

@home_bp.route('/es/notes', methods=['GET', 'POST'])
def es_notes():
    return _notes_handler(locale='es')
