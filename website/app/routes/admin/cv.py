import mimetypes

from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.i18n import t
from app.models.models import CvFile
from app.routes.admin import admin_bp
from app.services.rendercv_service import MAX_CV_YAML_BYTES, RenderCVError, render_yaml_to_pdf
from app.storage import storage

ALLOWED_EXTENSIONS = {'pdf'}
MAX_CV_BYTES = 10 * 1024 * 1024  # 10 MB
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_CV_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
PER_PAGE = 50

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]

SOURCES = ('upload', 'generated')


def _allowed(filename: str, extensions=ALLOWED_EXTENSIONS) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


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


def _read_cv_images(req) -> dict[str, bytes]:
    """Read images uploaded for the YAML to reference by filename (e.g. `photo: logo.png`)."""
    images = {}
    for file in req.files.getlist('cv_images'):
        if not file or not file.filename:
            continue
        name = secure_filename(file.filename)
        content = file.read()
        if not _allowed(name, IMAGE_EXTENSIONS) or len(content) > MAX_CV_IMAGE_BYTES:
            raise ValueError(t('flash.cv_image_rejected', name=file.filename))
        images[name] = content
    return images


def _images_prefix(cv_id: int) -> str:
    return f"cv/{cv_id}_images/"


def _delete_cv_images(cv_id: int) -> None:
    for path in storage.list(_images_prefix(cv_id)):
        storage.delete(path)


def _store_generated_cv(yaml_text: str, cv_id: int, language: str,
                        new_images: dict[str, bytes], removed: set[str] = frozenset()) -> tuple[str, str]:
    """Render the YAML (with the CV's stored images minus `removed`, plus any new ones) to a
    PDF and persist everything. Raises RenderCVError on failure, before anything is changed."""
    prefix = _images_prefix(cv_id)
    stored_paths = {path.rsplit('/', 1)[-1]: path for path in storage.list(prefix)}
    kept = {name: storage.get(path) for name, path in stored_paths.items() if name not in removed}
    pdf_bytes = render_yaml_to_pdf(yaml_text, {**kept, **new_images})
    yaml_path = f"cv/{cv_id}_{secure_filename(language)}.yaml"
    pdf_path = f"cv/{cv_id}_{secure_filename(language)}.pdf"
    storage.put(yaml_path, yaml_text, content_type='text/yaml')
    storage.put(pdf_path, pdf_bytes, content_type='application/pdf')
    for name in removed & stored_paths.keys():  # only names we listed, never raw form input
        storage.delete(stored_paths[name])
    for name, content in new_images.items():
        storage.put(prefix + name, content,
                    content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
    return yaml_path, pdf_path


def _render_form(**kwargs):
    """render_template for cv/form.html with the params every branch needs."""
    kwargs.setdefault('languages', LANGUAGES)
    cv = kwargs.get('cv')
    kwargs.setdefault('cv_images', storage.list(_images_prefix(cv.id)) if cv else [])
    return render_template('admin/cv/form.html', **kwargs)


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
            flash(t('flash.language_required'), 'error')
            return _render_form(cv=None)

        raw_source = request.form.get('source', 'upload')

        if raw_source == 'generated':
            source = 'generated'
            try:
                yaml_text = _read_yaml_input(request)
                images = _read_cv_images(request)
            except ValueError as exc:
                flash(str(exc), 'error')
                return _render_form(cv=None, submitted_source=source, submitted_language=language)

            if not yaml_text:
                flash(t('flash.yaml_required'), 'error')
                return _render_form(cv=None, submitted_source=source, submitted_language=language)
        else:
            source = 'upload'

        if source == 'generated':
            cv = CvFile(language=language, file_path='', source=source)
            db.session.add(cv)
            db.session.flush()

            try:
                yaml_path, pdf_path = _store_generated_cv(yaml_text, cv.id, language, images)
            except RenderCVError as exc:
                db.session.rollback()
                flash(t('flash.cv_generation_failed', exc=exc), 'error')
                return _render_form(cv=None, submitted_yaml=yaml_text, submitted_source=source,
                                     submitted_language=language)

            cv.yaml_path = yaml_path
            cv.file_path = pdf_path
        else:
            file = request.files.get('cv_file')
            if not file or not file.filename:
                flash(t('flash.pdf_required'), 'error')
                return _render_form(cv=None, submitted_source=source, submitted_language=language)

            cv = CvFile(language=language, file_path='', source=source)
            db.session.add(cv)
            db.session.flush()

            path = f"cv/{cv.id}_{secure_filename(language)}.pdf"
            if not _store_cv(file, path):
                db.session.rollback()
                flash(t('flash.pdf_rejected'), 'error')
                return _render_form(cv=None, submitted_source=source, submitted_language=language)
            cv.file_path = path

        db.session.commit()
        flash(t('flash.cv_uploaded', lang=language.upper()), 'success')
        return redirect(url_for('admin.cv_list'))

    return _render_form(cv=None)


# ── Edit ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/cv/<int:cv_id>/edit', methods=['GET', 'POST'])
@login_required
def cv_edit(cv_id):
    cv = db.session.get(CvFile, cv_id)
    if cv is None:
        flash(t('flash.cv_not_found'), 'error')
        return redirect(url_for('admin.cv_list'))

    if request.method == 'POST':
        language = request.form.get('language', '').strip()
        if not language:
            flash(t('flash.language_required'), 'error')
            return _render_form(cv=cv)

        raw_source = request.form.get('source', '').strip()
        cv.language = language
        images = {}
        removed = set()

        if raw_source == 'generated':
            source = 'generated'
            removed = set(request.form.getlist('cv_images_delete'))
            try:
                yaml_text = _read_yaml_input(request)
                images = _read_cv_images(request)
            except ValueError as exc:
                flash(str(exc), 'error')
                return _render_form(cv=cv, submitted_source=source)
        else:
            source = raw_source if raw_source in SOURCES else cv.source
            yaml_text = ''

        if source == 'generated':
            if not yaml_text and (images or removed) and cv.source == 'generated' and cv.yaml_path:
                # Only image changes submitted: re-render the stored YAML with them.
                yaml_text = storage.get(cv.yaml_path).decode('utf-8', errors='replace')
            if yaml_text:
                try:
                    yaml_path, pdf_path = _store_generated_cv(yaml_text, cv.id, language, images, removed)
                except RenderCVError as exc:
                    flash(t('flash.cv_generation_failed', exc=exc), 'error')
                    return _render_form(cv=cv, submitted_yaml=yaml_text, submitted_source=source)

                if cv.file_path and cv.file_path != pdf_path:
                    storage.delete(cv.file_path)
                if cv.yaml_path and cv.yaml_path != yaml_path:
                    storage.delete(cv.yaml_path)
                cv.file_path = pdf_path
                cv.yaml_path = yaml_path
                cv.source = 'generated'
            elif cv.source != 'generated' or not cv.yaml_path:
                flash(t('flash.yaml_required'), 'error')
                return _render_form(cv=cv, submitted_source=source)
            # else: staying generated, no new YAML submitted — keep existing files as-is.
        else:
            file = request.files.get('cv_file')
            if file and file.filename:
                new_path = f"cv/{cv.id}_{secure_filename(language)}.pdf"
                if not _store_cv(file, new_path):
                    flash(t('flash.pdf_rejected'), 'error')
                    return _render_form(cv=cv, submitted_source=source)
                if cv.file_path and cv.file_path != new_path:
                    storage.delete(cv.file_path)
                cv.file_path = new_path
            elif not cv.file_path:
                flash(t('flash.pdf_required'), 'error')
                return _render_form(cv=cv, submitted_source=source)

            if cv.yaml_path:
                storage.delete(cv.yaml_path)
                cv.yaml_path = None
            _delete_cv_images(cv.id)
            cv.source = 'upload'

        db.session.commit()
        flash(t('flash.cv_updated'), 'success')
        return redirect(url_for('admin.cv_list'))

    submitted_yaml = ''
    if cv.source == 'generated' and cv.yaml_path and storage.exists(cv.yaml_path):
        try:
            submitted_yaml = storage.get(cv.yaml_path).decode('utf-8', errors='replace')
        except Exception:
            submitted_yaml = ''

    return _render_form(cv=cv, submitted_yaml=submitted_yaml)


# ── Delete ────────────────────────────────────────────────────────────────────

@admin_bp.post('/cv/<int:cv_id>/delete')
@login_required
def cv_delete(cv_id):
    cv = db.session.get(CvFile, cv_id)
    if cv is None:
        flash(t('flash.cv_not_found'), 'error')
        return redirect(url_for('admin.cv_list'))

    if cv.yaml_path:
        storage.delete(cv.yaml_path)
    if cv.file_path:
        storage.delete(cv.file_path)
    _delete_cv_images(cv.id)

    lang = cv.language
    db.session.delete(cv)
    db.session.commit()
    flash(t('flash.cv_deleted', lang=lang.upper()), 'success')
    return redirect(url_for('admin.cv_list'))
