from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models.models import GalleryPhoto
from app.routes.admin import admin_bp
from app.storage import storage

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _allowed(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _store_image(file, dest_path: str) -> bool:
    """Validate and persist an uploaded image file. Returns True on success."""
    if not file or not file.filename:
        return False
    if not _allowed(file.filename):
        return False
    content = file.read()
    if len(content) > MAX_IMAGE_BYTES:
        return False
    storage.put(dest_path, content, content_type=file.content_type or 'image/jpeg')
    return True


# ── List ─────────────────────────────────────────────────────────────────────

@admin_bp.get('/gallery/')
@login_required
def gallery_list():
    photos = (
        GalleryPhoto.query
        .order_by(GalleryPhoto.created_at.desc())
        .all()
    )
    return render_template('admin/gallery/list.html', photos=photos)


# ── Create ────────────────────────────────────────────────────────────────────

@admin_bp.route('/gallery/create', methods=['GET', 'POST'])
@login_required
def gallery_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        image = request.files.get('image')

        if not title:
            flash('Title is required.', 'error')
            return render_template('admin/gallery/form.html', photo=None)
        if not image or not image.filename:
            flash('Image is required.', 'error')
            return render_template('admin/gallery/form.html', photo=None)

        has_es = request.form.get('has_es') == '1'
        title_es = request.form.get('title_es', '').strip() or None
        description_es = request.form.get('description_es', '').strip() or None

        photo = GalleryPhoto(
            title=title,
            description=request.form.get('description', '').strip() or None,
            has_es=has_es,
            title_es=title_es if has_es else None,
            description_es=description_es if has_es else None,
            image_path='',
        )
        db.session.add(photo)
        db.session.flush()  # get id before commit

        ext = secure_filename(image.filename).rsplit('.', 1)[-1].lower()
        path = f"gallery/{photo.id}.{ext}"
        if not _store_image(image, path):
            db.session.rollback()
            flash('Image rejected — invalid type or exceeds 5 MB.', 'error')
            return render_template('admin/gallery/form.html', photo=None)

        photo.image_path = path
        db.session.commit()
        flash(f'Photo "{photo.title}" created.', 'success')
        return redirect(url_for('admin.gallery_list'))

    return render_template('admin/gallery/form.html', photo=None)


# ── Edit ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/gallery/<int:photo_id>/edit', methods=['GET', 'POST'])
@login_required
def gallery_edit(photo_id):
    photo = db.session.get(GalleryPhoto, photo_id)
    if photo is None:
        flash('Photo not found.', 'error')
        return redirect(url_for('admin.gallery_list'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return render_template('admin/gallery/form.html', photo=photo)

        has_es = request.form.get('has_es') == '1'
        title_es = request.form.get('title_es', '').strip() or None
        description_es = request.form.get('description_es', '').strip() or None

        photo.title = title
        photo.description = request.form.get('description', '').strip() or None
        photo.has_es = has_es
        photo.title_es = title_es if has_es else None
        photo.description_es = description_es if has_es else None

        image = request.files.get('image')
        if image and image.filename:
            ext = secure_filename(image.filename).rsplit('.', 1)[-1].lower()
            new_path = f"gallery/{photo.id}.{ext}"
            if _store_image(image, new_path):
                if photo.image_path and photo.image_path != new_path:
                    storage.delete(photo.image_path)
                photo.image_path = new_path
            else:
                flash('Image rejected — invalid type or exceeds 5 MB.', 'error')

        db.session.commit()
        flash('Photo updated.', 'success')
        return redirect(url_for('admin.gallery_edit', photo_id=photo.id))

    return render_template('admin/gallery/form.html', photo=photo)


# ── Delete ────────────────────────────────────────────────────────────────────

@admin_bp.post('/gallery/<int:photo_id>/delete')
@login_required
def gallery_delete(photo_id):
    photo = db.session.get(GalleryPhoto, photo_id)
    if photo is None:
        flash('Photo not found.', 'error')
        return redirect(url_for('admin.gallery_list'))

    if photo.image_path:
        storage.delete(photo.image_path)

    title = photo.title
    db.session.delete(photo)
    db.session.commit()
    flash(f'Photo "{title}" deleted.', 'success')
    return redirect(url_for('admin.gallery_list'))
