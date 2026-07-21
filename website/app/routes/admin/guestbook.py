from flask import flash, redirect, render_template, url_for
from flask_login import login_required

from app import db
from app.models.models import GuestbookEntry
from app.routes.admin import admin_bp


@admin_bp.get('/guestbook/')
@login_required
def guestbook_list():
    entries = (
        GuestbookEntry.query
        .order_by(GuestbookEntry.created_at.desc())
        .all()
    )
    return render_template('admin/guestbook/list.html', entries=entries)


@admin_bp.post('/guestbook/<int:entry_id>/approve')
@login_required
def guestbook_approve(entry_id):
    entry = db.session.get(GuestbookEntry, entry_id)
    if entry is None:
        flash('Entrada no encontrada.', 'error')
        return redirect(url_for('admin.guestbook_list'))

    entry.approved = True
    db.session.commit()
    flash('Entrada aprobada y publicada.', 'success')
    return redirect(url_for('admin.guestbook_list'))


@admin_bp.post('/guestbook/<int:entry_id>/unapprove')
@login_required
def guestbook_unapprove(entry_id):
    entry = db.session.get(GuestbookEntry, entry_id)
    if entry is None:
        flash('Entrada no encontrada.', 'error')
        return redirect(url_for('admin.guestbook_list'))

    entry.approved = False
    db.session.commit()
    flash('Entrada oculta del guestbook público.', 'success')
    return redirect(url_for('admin.guestbook_list'))


@admin_bp.post('/guestbook/<int:entry_id>/delete')
@login_required
def guestbook_delete(entry_id):
    entry = db.session.get(GuestbookEntry, entry_id)
    if entry is None:
        flash('Entrada no encontrada.', 'error')
        return redirect(url_for('admin.guestbook_list'))

    db.session.delete(entry)
    db.session.commit()
    flash('Entrada eliminada.', 'success')
    return redirect(url_for('admin.guestbook_list'))
