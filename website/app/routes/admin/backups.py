from datetime import datetime
from io import BytesIO

from flask import flash, redirect, render_template, request, send_file, url_for
from flask_login import login_required

from app import db
from app.models.models import Backup
from app.routes.admin import admin_bp
from app.services.backup_service import BackupError, generate_data_dump
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
        dump_bytes = generate_data_dump()
    except BackupError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('admin.backups_list'))

    filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
    path = f'backups/{filename}'
    storage.put(path, dump_bytes, content_type='application/sql')

    backup = Backup(filename=filename, file_path=path, size_bytes=len(dump_bytes))
    db.session.add(backup)
    db.session.commit()

    flash(f'Backup "{filename}" generated ({len(dump_bytes) // 1024} KB).', 'success')
    return redirect(url_for('admin.backups_list'))


@admin_bp.get('/backups/<int:backup_id>/download')
@login_required
def backups_download(backup_id):
    backup = db.session.get(Backup, backup_id)
    if backup is None or not storage.exists(backup.file_path):
        flash('Backup not found.', 'error')
        return redirect(url_for('admin.backups_list'))

    data = storage.get(backup.file_path)
    return send_file(
        BytesIO(data),
        mimetype='application/sql',
        as_attachment=True,
        download_name=backup.filename,
    )


@admin_bp.post('/backups/<int:backup_id>/delete')
@login_required
def backups_delete(backup_id):
    backup = db.session.get(Backup, backup_id)
    if backup is None:
        flash('Backup not found.', 'error')
        return redirect(url_for('admin.backups_list'))

    storage.delete(backup.file_path)
    filename = backup.filename
    db.session.delete(backup)
    db.session.commit()
    flash(f'Backup "{filename}" deleted.', 'success')
    return redirect(url_for('admin.backups_list'))
