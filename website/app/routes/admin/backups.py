from io import BytesIO

from flask import flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from app import db
from app.i18n import t
from app.models.models import Backup
from app.routes.admin import admin_bp
from app.services.backup_service import BackupError, create_backup
from app.storage import storage

PER_PAGE = 50


@admin_bp.get('/backups/')
@login_required
def backups_list():
    page = max(request.args.get('page', 1, type=int), 1)
    pagination = Backup.query.order_by(Backup.created_at.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    return render_template('admin/backups/list.html', pagination=pagination, backups=pagination.items)


@admin_bp.post('/backups/generate')
@login_required
def backups_generate():
    try:
        backup = create_backup()
    except BackupError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin.backups_list'))

    flash(t('flash.backup_generated', filename=backup.filename, kb=backup.size_bytes // 1024), 'success')
    return redirect(url_for('admin.backups_list'))


@admin_bp.get('/backups/<int:backup_id>/download')
@login_required
def backups_download(backup_id):
    backup = db.session.get(Backup, backup_id)
    if backup is None or not storage.exists(backup.file_path):
        flash(t('flash.backup_not_found'), 'error')
        return redirect(url_for('admin.backups_list'))

    data = storage.get(backup.file_path)
    return send_file(
        BytesIO(data),
        # Older backups were stored as plain .sql before dumps were gzipped.
        mimetype='application/gzip' if backup.filename.endswith('.gz') else 'application/sql',
        as_attachment=True,
        download_name=backup.filename,
    )


@admin_bp.post('/backups/<int:backup_id>/delete')
@login_required
def backups_delete(backup_id):
    backup = db.session.get(Backup, backup_id)
    if backup is None:
        flash(t('flash.backup_not_found'), 'error')
        return redirect(url_for('admin.backups_list'))

    storage.delete(backup.file_path)
    filename = backup.filename
    db.session.delete(backup)
    db.session.commit()
    flash(t('flash.backup_deleted', filename=filename), 'success')
    return redirect(url_for('admin.backups_list'))
