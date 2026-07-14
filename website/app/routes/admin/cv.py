from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models.models import CvFile
from app.routes.admin import admin_bp
from app.services.rendercv_service import MAX_CV_YAML_BYTES, RenderCVError, render_yaml_to_pdf
from app.storage import storage

ALLOWED_EXTENSIONS = {'pdf'}
MAX_CV_BYTES = 10 * 1024 * 1024  # 10 MB

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


# ── List ──────────────────────────────────────────────────────────────────────

@admin_bp.get('/cv/')
@login_required
def cv_list():
    cvs = CvFile.query.order_by(CvFile.uploaded_at.desc()).all()
    return render_template('admin/cv/list.html', cvs=cvs)


# ── Upload ────────────────────────────────────────────────────────────────────

@admin_bp.route('/cv/upload', methods=['GET', 'POST'])
@login_required
def cv_upload():
    if request.method == 'POST':
        language = request.form.get('language', '').strip()
        if not language:
            flash('Language is required.', 'error')
            return render_template('admin/cv/form.html', cv=None, languages=LANGUAGES)

        source = request.form.get('source', 'upload')
        if source not in SOURCES:
            source = 'upload'

        if source == 'generated':
            try:
                yaml_text = _read_yaml_input(request)
            except ValueError as exc:
                flash(str(exc), 'error')
                return render_template('admin/cv/form.html', cv=None, languages=LANGUAGES, submitted_source=source)

            if not yaml_text:
                flash('YAML content is required.', 'error')
                return render_template('admin/cv/form.html', cv=None, languages=LANGUAGES, submitted_source=source)

            cv = CvFile(language=language, file_path='', source=source)
            db.session.add(cv)
            db.session.flush()

            try:
                yaml_path, pdf_path = _store_generated_cv(yaml_text, cv.id, language)
            except RenderCVError as exc:
                db.session.rollback()
                flash(f'CV generation failed: {exc}', 'error')
                return render_template(
                    'admin/cv/form.html', cv=None, languages=LANGUAGES,
                    submitted_yaml=yaml_text, submitted_source=source,
                )

            cv.yaml_path = yaml_path
            cv.file_path = pdf_path
        else:
            file = request.files.get('cv_file')
            if not file or not file.filename:
                flash('A PDF file is required.', 'error')
                return render_template('admin/cv/form.html', cv=None, languages=LANGUAGES, submitted_source=source)

            cv = CvFile(language=language, file_path='', source=source)
            db.session.add(cv)
            db.session.flush()

            path = f"cv/{cv.id}_{secure_filename(language)}.pdf"
            if not _store_cv(file, path):
                db.session.rollback()
                flash('File rejected — must be a PDF and no larger than 10 MB.', 'error')
                return render_template('admin/cv/form.html', cv=None, languages=LANGUAGES, submitted_source=source)
            cv.file_path = path

        db.session.commit()
        flash(f'CV ({language.upper()}) uploaded successfully.', 'success')
        return redirect(url_for('admin.cv_list'))

    return render_template('admin/cv/form.html', cv=None, languages=LANGUAGES)


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
            return render_template('admin/cv/form.html', cv=cv, languages=LANGUAGES)

        source = request.form.get('source', '').strip()
        if source not in SOURCES:
            source = cv.source

        cv.language = language

        if source == 'generated':
            try:
                yaml_text = _read_yaml_input(request)
            except ValueError as exc:
                flash(str(exc), 'error')
                return render_template('admin/cv/form.html', cv=cv, languages=LANGUAGES, submitted_source=source)

            if yaml_text:
                try:
                    yaml_path, pdf_path = _store_generated_cv(yaml_text, cv.id, language)
                except RenderCVError as exc:
                    flash(f'CV generation failed: {exc}', 'error')
                    return render_template(
                        'admin/cv/form.html', cv=cv, languages=LANGUAGES,
                        submitted_yaml=yaml_text, submitted_source=source,
                    )
                if cv.file_path and cv.file_path != pdf_path:
                    storage.delete(cv.file_path)
                if cv.yaml_path and cv.yaml_path != yaml_path:
                    storage.delete(cv.yaml_path)
                cv.file_path = pdf_path
                cv.yaml_path = yaml_path
                cv.source = 'generated'
            elif cv.source != 'generated' or not cv.yaml_path:
                flash('YAML content is required.', 'error')
                return render_template('admin/cv/form.html', cv=cv, languages=LANGUAGES, submitted_source=source)
            # else: staying generated, no new YAML submitted — keep existing files as-is.
        else:
            file = request.files.get('cv_file')
            if file and file.filename:
                new_path = f"cv/{cv.id}_{secure_filename(language)}.pdf"
                if not _store_cv(file, new_path):
                    flash('File rejected — must be a PDF and no larger than 10 MB.', 'error')
                    return render_template('admin/cv/form.html', cv=cv, languages=LANGUAGES, submitted_source=source)
                if cv.file_path and cv.file_path != new_path:
                    storage.delete(cv.file_path)
                cv.file_path = new_path
            elif not cv.file_path:
                flash('A PDF file is required.', 'error')
                return render_template('admin/cv/form.html', cv=cv, languages=LANGUAGES, submitted_source=source)

            if cv.yaml_path:
                storage.delete(cv.yaml_path)
                cv.yaml_path = None
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
    return render_template('admin/cv/form.html', cv=cv, languages=LANGUAGES, submitted_yaml=submitted_yaml)


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

    lang = cv.language
    db.session.delete(cv)
    db.session.commit()
    flash(f'CV ({lang.upper()}) deleted.', 'success')
    return redirect(url_for('admin.cv_list'))
