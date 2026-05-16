from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models.models import ExtraPortfolioImage, PortfolioProject
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

@admin_bp.get('/projects/')
@login_required
def projects_list():
    projects = (
        PortfolioProject.query
        .order_by(PortfolioProject.created_at.desc())
        .all()
    )
    return render_template('admin/projects/list.html', projects=projects)


# ── Create ────────────────────────────────────────────────────────────────────

@admin_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
def projects_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return render_template('admin/projects/form.html', project=None, extra_images=[])

        project = PortfolioProject(
            title=title,
            description=request.form.get('description', '').strip() or None,
            project_url=request.form.get('project_url', '').strip() or None,
            github_repo_url=request.form.get('github_repo_url', '').strip() or None,
        )
        db.session.add(project)
        db.session.flush()  # get id before commit

        cover = request.files.get('cover_image')
        if cover and cover.filename:
            ext = secure_filename(cover.filename).rsplit('.', 1)[-1].lower()
            path = f"portfolio/covers/{project.id}.{ext}"
            if _store_image(cover, path):
                project.image_path = path
            else:
                flash('Cover image rejected — invalid type or exceeds 5 MB.', 'error')

        db.session.commit()
        flash(f'Project "{project.title}" created.', 'success')
        return redirect(url_for('admin.projects_list'))

    return render_template('admin/projects/form.html', project=None, extra_images=[])


# ── Edit ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def projects_edit(project_id):
    project = db.session.get(PortfolioProject, project_id)
    if project is None:
        flash('Project not found.', 'error')
        return redirect(url_for('admin.projects_list'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return render_template('admin/projects/form.html',
                                   project=project, extra_images=project.extra_images)

        project.title = title
        project.description = request.form.get('description', '').strip() or None
        project.project_url = request.form.get('project_url', '').strip() or None
        project.github_repo_url = request.form.get('github_repo_url', '').strip() or None

        cover = request.files.get('cover_image')
        if cover and cover.filename:
            ext = secure_filename(cover.filename).rsplit('.', 1)[-1].lower()
            new_path = f"portfolio/covers/{project.id}.{ext}"
            if _store_image(cover, new_path):
                if project.image_path and project.image_path != new_path:
                    storage.delete(project.image_path)
                project.image_path = new_path
            else:
                flash('Cover image rejected — invalid type or exceeds 5 MB.', 'error')

        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('admin.projects_edit', project_id=project.id))

    return render_template('admin/projects/form.html',
                           project=project, extra_images=project.extra_images)


# ── Delete ────────────────────────────────────────────────────────────────────

@admin_bp.post('/projects/<int:project_id>/delete')
@login_required
def projects_delete(project_id):
    project = db.session.get(PortfolioProject, project_id)
    if project is None:
        flash('Project not found.', 'error')
        return redirect(url_for('admin.projects_list'))

    if project.image_path:
        storage.delete(project.image_path)
    for img in project.extra_images:
        storage.delete(img.image_path)

    title = project.title
    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{title}" deleted.', 'success')
    return redirect(url_for('admin.projects_list'))


# ── Extra images ──────────────────────────────────────────────────────────────

@admin_bp.post('/projects/<int:project_id>/images')
@login_required
def projects_add_image(project_id):
    project = db.session.get(PortfolioProject, project_id)
    if project is None:
        flash('Project not found.', 'error')
        return redirect(url_for('admin.projects_list'))

    file = request.files.get('image')
    if not file or not file.filename:
        flash('No image selected.', 'error')
        return redirect(url_for('admin.projects_edit', project_id=project_id))

    filename = secure_filename(file.filename)
    path = f"portfolio/extras/{project_id}/{filename}"
    if _store_image(file, path):
        db.session.add(ExtraPortfolioImage(project_id=project_id, image_path=path))
        db.session.commit()
        flash('Image added.', 'success')
    else:
        flash('Image rejected — invalid type or exceeds 5 MB.', 'error')

    return redirect(url_for('admin.projects_edit', project_id=project_id))


@admin_bp.post('/projects/<int:project_id>/images/<int:image_id>/delete')
@login_required
def projects_delete_image(project_id, image_id):
    img = db.session.get(ExtraPortfolioImage, image_id)
    if img and img.project_id == project_id:
        storage.delete(img.image_path)
        db.session.delete(img)
        db.session.commit()
        flash('Image removed.', 'success')
    return redirect(url_for('admin.projects_edit', project_id=project_id))
