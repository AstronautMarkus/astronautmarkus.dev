import json

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models.models import CvFile
from app.routes.admin import admin_bp
from app.services.rendercv_service import (
    AVAILABLE_THEMES,
    MAX_CV_YAML_BYTES,
    SOCIAL_NETWORKS,
    RenderCVError,
    build_yaml_from_builder_data,
    render_yaml_to_pdf,
)
from app.storage import storage

ALLOWED_EXTENSIONS = {'pdf'}
MAX_CV_BYTES = 10 * 1024 * 1024  # 10 MB
PER_PAGE = 50

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]

SOURCES = ('upload', 'generated')


def _allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _store_cv(file, dest_path: str) -> bool:
    """Validate and persist an uploaded CV PDF. Returns True on success."""
    if not file or not file.filename:
        return False
    if not _allowed(file.filename):
        return False
    content = file.read()
    if len(content) > MAX_CV_BYTES:
        return False
    storage.put(dest_path, content, content_type='application/pdf')
    return True


def _read_yaml_input(req) -> str:
    """Read YAML from an uploaded file or a textarea, whichever is present."""
    yaml_file = req.files.get('cv_yaml_file')
    if yaml_file and yaml_file.filename:
        content = yaml_file.read()
        if len(content) > MAX_CV_YAML_BYTES:
            raise ValueError(f'YAML file is too large — max {MAX_CV_YAML_BYTES // (1024 * 1024)} MB.')
        return content.decode('utf-8', errors='replace')
    return (req.form.get('cv_yaml') or '').strip()


def _store_generated_cv(yaml_text: str, cv_id: int, language: str) -> tuple[str, str]:
    """Render the YAML to a PDF and persist both files. Raises RenderCVError on failure."""
    pdf_bytes = render_yaml_to_pdf(yaml_text)
    yaml_path = f"cv/{cv_id}_{secure_filename(language)}.yaml"
    pdf_path = f"cv/{cv_id}_{secure_filename(language)}.pdf"
    storage.put(yaml_path, yaml_text, content_type='text/yaml')
    storage.put(pdf_path, pdf_bytes, content_type='application/pdf')
    return yaml_path, pdf_path


def _builder_sidecar_path(cv_id: int, language: str) -> str:
    """Path to the raw CV Builder JSON kept alongside a generated CV's yaml/pdf,
    so the builder form can be rehydrated exactly when editing it again."""
    return f"cv/{cv_id}_{secure_filename(language)}.builder.json"


def _render_form(**kwargs):
    """render_template for cv/form.html with the params every branch needs."""
    kwargs.setdefault('languages', LANGUAGES)
    kwargs.setdefault('themes', AVAILABLE_THEMES)
    kwargs.setdefault('social_networks', SOCIAL_NETWORKS)
    kwargs.setdefault('builder_initial_data', None)
    return render_template('admin/cv/form.html', **kwargs)


def _parse_builder_json(raw_text: str) -> dict:
    """Parse the builder's submitted JSON blob. Malformed input becomes an empty
    dict (the caller's own field-level validation then reports what's missing)."""
    try:
        data = json.loads(raw_text) if raw_text else {}
    except (ValueError, TypeError):
        flash('Could not read the builder data — please try again.', 'warning')
        return {}
    return data if isinstance(data, dict) else {}


# ── List ──────────────────────────────────────────────────────────────────────

@admin_bp.get('/cv/')
@login_required
def cv_list():
    page = max(request.args.get('page', 1, type=int), 1)
    pagination = CvFile.query.order_by(CvFile.uploaded_at.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    return render_template('admin/cv/list.html', pagination=pagination, cvs=pagination.items)


# ── Upload ────────────────────────────────────────────────────────────────────

@admin_bp.route('/cv/upload', methods=['GET', 'POST'])
@login_required
def cv_upload():
    if request.method == 'POST':
        language = request.form.get('language', '').strip()
        if not language:
            flash('Language is required.', 'error')
            return _render_form(cv=None)

        raw_source = request.form.get('source', 'upload')
        builder_data = None

        if raw_source == 'builder':
            builder_data = _parse_builder_json(request.form.get('cv_builder_json', ''))
            if not (builder_data.get('header') or {}).get('name', '').strip():
                flash('Name is required.', 'error')
                return _render_form(cv=None, submitted_source='builder', builder_initial_data=builder_data,
                                     submitted_language=language)

            yaml_text, builder_warnings = build_yaml_from_builder_data(builder_data, language)
            for w in builder_warnings:
                flash(w, 'warning')
            source = 'generated'
        elif raw_source == 'generated':
            source = 'generated'
            try:
                yaml_text = _read_yaml_input(request)
            except ValueError as exc:
                flash(str(exc), 'error')
                return _render_form(cv=None, submitted_source=source, submitted_language=language)

            if not yaml_text:
                flash('YAML content is required.', 'error')
                return _render_form(cv=None, submitted_source=source, submitted_language=language)
        else:
            source = 'upload'

        if source == 'generated':
            cv = CvFile(language=language, file_path='', source=source)
            db.session.add(cv)
            db.session.flush()

            try:
                yaml_path, pdf_path = _store_generated_cv(yaml_text, cv.id, language)
            except RenderCVError as exc:
                db.session.rollback()
                flash(f'CV generation failed: {exc}', 'error')
                if raw_source == 'builder':
                    return _render_form(cv=None, submitted_source='builder', builder_initial_data=builder_data,
                                         submitted_language=language)
                return _render_form(cv=None, submitted_yaml=yaml_text, submitted_source=source,
                                     submitted_language=language)

            cv.yaml_path = yaml_path
            cv.file_path = pdf_path

            if raw_source == 'builder':
                storage.put(_builder_sidecar_path(cv.id, language), json.dumps(builder_data),
                            content_type='application/json')
        else:
            file = request.files.get('cv_file')
            if not file or not file.filename:
                flash('A PDF file is required.', 'error')
                return _render_form(cv=None, submitted_source=source, submitted_language=language)

            cv = CvFile(language=language, file_path='', source=source)
            db.session.add(cv)
            db.session.flush()

            path = f"cv/{cv.id}_{secure_filename(language)}.pdf"
            if not _store_cv(file, path):
                db.session.rollback()
                flash('File rejected — must be a PDF and no larger than 10 MB.', 'error')
                return _render_form(cv=None, submitted_source=source, submitted_language=language)
            cv.file_path = path

        db.session.commit()
        flash(f'CV ({language.upper()}) uploaded successfully.', 'success')
        return redirect(url_for('admin.cv_list'))

    return _render_form(cv=None)


# ── Edit ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/cv/<int:cv_id>/edit', methods=['GET', 'POST'])
@login_required
def cv_edit(cv_id):
    cv = db.session.get(CvFile, cv_id)
    if cv is None:
        flash('CV not found.', 'error')
        return redirect(url_for('admin.cv_list'))

    if request.method == 'POST':
        language = request.form.get('language', '').strip()
        if not language:
            flash('Language is required.', 'error')
            return _render_form(cv=cv)

        raw_source = request.form.get('source', '').strip()
        builder_data = None
        cv.language = language

        if raw_source == 'builder':
            builder_data = _parse_builder_json(request.form.get('cv_builder_json', ''))
            if not (builder_data.get('header') or {}).get('name', '').strip():
                flash('Name is required.', 'error')
                return _render_form(cv=cv, submitted_source='builder', builder_initial_data=builder_data)

            yaml_text, builder_warnings = build_yaml_from_builder_data(builder_data, language)
            for w in builder_warnings:
                flash(w, 'warning')
            source = 'generated'
        elif raw_source == 'generated':
            source = 'generated'
            try:
                yaml_text = _read_yaml_input(request)
            except ValueError as exc:
                flash(str(exc), 'error')
                return _render_form(cv=cv, submitted_source=source)
        else:
            source = raw_source if raw_source in SOURCES else cv.source
            yaml_text = ''

        if source == 'generated':
            if yaml_text:
                try:
                    yaml_path, pdf_path = _store_generated_cv(yaml_text, cv.id, language)
                except RenderCVError as exc:
                    flash(f'CV generation failed: {exc}', 'error')
                    if raw_source == 'builder':
                        return _render_form(cv=cv, submitted_source='builder', builder_initial_data=builder_data)
                    return _render_form(cv=cv, submitted_yaml=yaml_text, submitted_source=source)

                if cv.file_path and cv.file_path != pdf_path:
                    storage.delete(cv.file_path)
                if cv.yaml_path and cv.yaml_path != yaml_path:
                    storage.delete(cv.yaml_path)
                cv.file_path = pdf_path
                cv.yaml_path = yaml_path
                cv.source = 'generated'

                sidecar = _builder_sidecar_path(cv.id, language)
                if raw_source == 'builder':
                    storage.put(sidecar, json.dumps(builder_data), content_type='application/json')
                elif storage.exists(sidecar):
                    storage.delete(sidecar)
            elif cv.source != 'generated' or not cv.yaml_path:
                flash('YAML content is required.', 'error')
                return _render_form(cv=cv, submitted_source=source)
            # else: staying generated, no new YAML submitted — keep existing files as-is.
        else:
            file = request.files.get('cv_file')
            if file and file.filename:
                new_path = f"cv/{cv.id}_{secure_filename(language)}.pdf"
                if not _store_cv(file, new_path):
                    flash('File rejected — must be a PDF and no larger than 10 MB.', 'error')
                    return _render_form(cv=cv, submitted_source=source)
                if cv.file_path and cv.file_path != new_path:
                    storage.delete(cv.file_path)
                cv.file_path = new_path
            elif not cv.file_path:
                flash('A PDF file is required.', 'error')
                return _render_form(cv=cv, submitted_source=source)

            if cv.yaml_path:
                storage.delete(cv.yaml_path)
                cv.yaml_path = None
            sidecar = _builder_sidecar_path(cv.id, language)
            if storage.exists(sidecar):
                storage.delete(sidecar)
            cv.source = 'upload'

        db.session.commit()
        flash('CV updated successfully.', 'success')
        return redirect(url_for('admin.cv_list'))

    submitted_yaml = ''
    if cv.source == 'generated' and cv.yaml_path and storage.exists(cv.yaml_path):
        try:
            submitted_yaml = storage.get(cv.yaml_path).decode('utf-8', errors='replace')
        except Exception:
            submitted_yaml = ''

    builder_initial_data = None
    sidecar = _builder_sidecar_path(cv.id, cv.language)
    if cv.source == 'generated' and storage.exists(sidecar):
        try:
            builder_initial_data = json.loads(storage.get(sidecar).decode('utf-8', errors='replace'))
        except Exception:
            builder_initial_data = None

    return _render_form(cv=cv, submitted_yaml=submitted_yaml, builder_initial_data=builder_initial_data)


# ── Delete ────────────────────────────────────────────────────────────────────

@admin_bp.post('/cv/<int:cv_id>/delete')
@login_required
def cv_delete(cv_id):
    cv = db.session.get(CvFile, cv_id)
    if cv is None:
        flash('CV not found.', 'error')
        return redirect(url_for('admin.cv_list'))

    if cv.yaml_path:
        storage.delete(cv.yaml_path)
    if cv.file_path:
        storage.delete(cv.file_path)
    sidecar = _builder_sidecar_path(cv.id, cv.language)
    if storage.exists(sidecar):
        storage.delete(sidecar)

    lang = cv.language
    db.session.delete(cv)
    db.session.commit()
    flash(f'CV ({lang.upper()}) deleted.', 'success')
    return redirect(url_for('admin.cv_list'))
