from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models.models import CvFile
from app.routes.admin import admin_bp
from app.storage import storage

ALLOWED_EXTENSIONS = {'pdf'}
MAX_CV_BYTES = 10 * 1024 * 1024  # 10 MB

LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
]


def _allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _store_cv(file, dest_path: str) -> bool:
    """Validate and persist an uploaded CV file. Returns True on success."""
    if not file or not file.filename:
        return False
    if not _allowed(file.filename):
        return False
    content = file.read()
    if len(content) > MAX_CV_BYTES:
        return False
    storage.put(dest_path, content, content_type='application/pdf')
    return True


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

        file = request.files.get('cv_file')
        if not file or not file.filename:
            flash('A PDF file is required.', 'error')
            return render_template('admin/cv/form.html', cv=None, languages=LANGUAGES)

        # Temporarily flush to get an ID for the path
        cv = CvFile(language=language, file_path='')
        db.session.add(cv)
        db.session.flush()

        path = f"cv/{cv.id}_{secure_filename(language)}.pdf"
        if not _store_cv(file, path):
            db.session.rollback()
            flash('File rejected — must be a PDF and no larger than 10 MB.', 'error')
            return render_template('admin/cv/form.html', cv=None, languages=LANGUAGES)

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

        cv.language = language

        file = request.files.get('cv_file')
        if file and file.filename:
            new_path = f"cv/{cv.id}_{secure_filename(language)}.pdf"
            if _store_cv(file, new_path):
                if cv.file_path and cv.file_path != new_path:
                    storage.delete(cv.file_path)
                cv.file_path = new_path
            else:
                flash('File rejected — must be a PDF and no larger than 10 MB.', 'error')
                return render_template('admin/cv/form.html', cv=cv, languages=LANGUAGES)

        db.session.commit()
        flash('CV updated successfully.', 'success')
        return redirect(url_for('admin.cv_list'))

    return render_template('admin/cv/form.html', cv=cv, languages=LANGUAGES)


# ── Delete ────────────────────────────────────────────────────────────────────

@admin_bp.post('/cv/<int:cv_id>/delete')
@login_required
def cv_delete(cv_id):
    cv = db.session.get(CvFile, cv_id)
    if cv is None:
        flash('CV not found.', 'error')
        return redirect(url_for('admin.cv_list'))

    if cv.file_path:
        storage.delete(cv.file_path)

    lang = cv.language
    db.session.delete(cv)
    db.session.commit()
    flash(f'CV ({lang.upper()}) deleted.', 'success')
    return redirect(url_for('admin.cv_list'))
