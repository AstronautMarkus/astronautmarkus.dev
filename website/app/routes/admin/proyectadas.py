from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.i18n import t
from app.models.models import Proyectada
from app.routes.admin import admin_bp

PER_PAGE = 50


# ── List ─────────────────────────────────────────────────────────────────────

@admin_bp.get('/proyectadas/')
@login_required
def proyectadas_list():
    page = max(request.args.get('page', 1, type=int), 1)
    pagination = Proyectada.query.order_by(Proyectada.created_at.desc()).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    return render_template('admin/proyectadas/list.html', pagination=pagination, items=pagination.items)


@admin_bp.post('/proyectadas/bulk-delete')
@login_required
def proyectadas_bulk_delete():
    ids = request.form.getlist('item_ids', type=int)
    if ids:
        deleted = (
            Proyectada.query
            .filter(Proyectada.id.in_(ids))
            .delete(synchronize_session=False)
        )
        db.session.commit()
        flash(t('flash.proyectadas_bulk_deleted', n=deleted), 'success')
    else:
        flash(t('flash.no_items_selected'), 'error')
    return redirect(url_for('admin.proyectadas_list'))


# ── Create ────────────────────────────────────────────────────────────────────

@admin_bp.route('/proyectadas/create', methods=['GET', 'POST'])
@login_required
def proyectadas_create():
    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        if not text:
            flash(t('flash.en_text_required'), 'error')
            return render_template('admin/proyectadas/form.html', item=None)
        if len(text) > 10000:
            flash(t('flash.text_too_long'), 'error')
            return render_template('admin/proyectadas/form.html', item=None)

        has_es = request.form.get('has_es') == '1'
        text_es = request.form.get('text_es', '').strip() or None
        published = request.form.get('published') == '1'

        item = Proyectada(
            text=text,
            has_es=has_es,
            text_es=text_es if has_es else None,
            published=published,
        )
        db.session.add(item)
        db.session.commit()
        flash(t('flash.proyectada_created'), 'success')
        return redirect(url_for('admin.proyectadas_list'))

    return render_template('admin/proyectadas/form.html', item=None)


# ── Edit ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/proyectadas/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def proyectadas_edit(item_id):
    item = db.session.get(Proyectada, item_id)
    if item is None:
        flash(t('flash.proyectada_not_found'), 'error')
        return redirect(url_for('admin.proyectadas_list'))

    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        if not text:
            flash(t('flash.en_text_required'), 'error')
            return render_template('admin/proyectadas/form.html', item=item)
        if len(text) > 10000:
            flash(t('flash.text_too_long'), 'error')
            return render_template('admin/proyectadas/form.html', item=item)

        has_es = request.form.get('has_es') == '1'
        text_es = request.form.get('text_es', '').strip() or None

        item.text = text
        item.has_es = has_es
        item.text_es = text_es if has_es else None
        item.published = request.form.get('published') == '1'

        db.session.commit()
        flash(t('flash.proyectada_updated'), 'success')
        return redirect(url_for('admin.proyectadas_list'))

    return render_template('admin/proyectadas/form.html', item=item)


# ── Delete ────────────────────────────────────────────────────────────────────

@admin_bp.post('/proyectadas/<int:item_id>/delete')
@login_required
def proyectadas_delete(item_id):
    item = db.session.get(Proyectada, item_id)
    if item is None:
        flash(t('flash.proyectada_not_found'), 'error')
        return redirect(url_for('admin.proyectadas_list'))

    db.session.delete(item)
    db.session.commit()
    flash(t('flash.proyectada_deleted'), 'success')
    return redirect(url_for('admin.proyectadas_list'))
