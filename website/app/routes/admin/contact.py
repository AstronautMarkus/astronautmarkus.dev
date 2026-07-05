from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models.models import BlockedSender, ContactMessage, MailTemplate
from app.routes.admin import admin_bp

# ─── Inbox ────────────────────────────────────────────────────────────────────

@admin_bp.get('/contact/')
@login_required
def contact_inbox():
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    unread = sum(1 for m in messages if not m.is_read)
    return render_template('admin/contact/inbox.html', messages=messages, unread=unread)


@admin_bp.get('/contact/<int:message_id>')
@login_required
def contact_message_detail(message_id):
    entry = db.session.get(ContactMessage, message_id)
    if entry is None:
        flash('Message not found.', 'error')
        return redirect(url_for('admin.contact_inbox'))
    if not entry.is_read:
        entry.is_read = True
        db.session.commit()
    return render_template('admin/contact/message_detail.html', entry=entry)


@admin_bp.post('/contact/<int:message_id>/delete')
@login_required
def contact_message_delete(message_id):
    entry = db.session.get(ContactMessage, message_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        flash('Message deleted.', 'success')
    return redirect(url_for('admin.contact_inbox'))


@admin_bp.post('/contact/bulk-delete')
@login_required
def contact_messages_bulk_delete():
    ids = request.form.getlist('message_ids', type=int)
    if ids:
        deleted = (
            ContactMessage.query
            .filter(ContactMessage.id.in_(ids))
            .delete(synchronize_session=False)
        )
        db.session.commit()
        flash(f'{deleted} message(s) deleted.', 'success')
    else:
        flash('No messages selected.', 'error')
    return redirect(url_for('admin.contact_inbox'))


@admin_bp.post('/contact/<int:message_id>/block-sender')
@login_required
def contact_message_block_sender(message_id):
    entry = db.session.get(ContactMessage, message_id)
    if entry is None:
        flash('Message not found.', 'error')
        return redirect(url_for('admin.contact_inbox'))

    email = entry.email.lower()
    if not BlockedSender.query.filter_by(email=email).first():
        db.session.add(BlockedSender(email=email, reason='manual'))

    deleted = (
        ContactMessage.query
        .filter(db.func.lower(ContactMessage.email) == email)
        .delete(synchronize_session=False)
    )
    db.session.commit()
    flash(f'Blocked {email} and deleted {deleted} message(s).', 'success')
    return redirect(url_for('admin.contact_inbox'))


# ─── Blocked senders ───────────────────────────────────────────────────────────

@admin_bp.get('/contact/blocked/')
@login_required
def blocked_senders():
    blocked = BlockedSender.query.order_by(BlockedSender.created_at.desc()).all()
    return render_template('admin/contact/blocked_senders.html', blocked=blocked)


@admin_bp.post('/contact/blocked/add')
@login_required
def blocked_sender_add():
    email = request.form.get('email', '').strip().lower()
    ip_address = request.form.get('ip_address', '').strip()

    if not email and not ip_address:
        flash('Provide an email and/or an IP address.', 'error')
        return redirect(url_for('admin.blocked_senders'))

    db.session.add(BlockedSender(
        email=email or None,
        ip_address=ip_address or None,
        reason='manual',
    ))
    db.session.commit()
    flash('Sender blocked.', 'success')
    return redirect(url_for('admin.blocked_senders'))


@admin_bp.post('/contact/blocked/<int:blocked_id>/delete')
@login_required
def blocked_sender_delete(blocked_id):
    entry = db.session.get(BlockedSender, blocked_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        flash('Sender unblocked.', 'success')
    return redirect(url_for('admin.blocked_senders'))


# ─── Mail templates ───────────────────────────────────────────────────────────

@admin_bp.get('/contact/mail-templates/')
@login_required
def contact_mail_templates():
    templates = MailTemplate.query.order_by(MailTemplate.slug, MailTemplate.language).all()
    return render_template('admin/contact/mail_templates.html', templates=templates)


@admin_bp.route('/contact/mail-templates/<int:template_id>/edit', methods=['GET', 'POST'])
@login_required
def contact_mail_template_edit(template_id):
    tpl = db.session.get(MailTemplate, template_id)
    if tpl is None:
        flash('Template not found.', 'error')
        return redirect(url_for('admin.contact_mail_templates'))

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        body_html = request.form.get('body_html', '').strip()
        description = request.form.get('description', '').strip()

        if not subject or not body_html:
            flash('Subject and body are required.', 'error')
            return render_template('admin/contact/mail_template_form.html', tpl=tpl)

        tpl.subject = subject
        tpl.body_html = body_html
        tpl.description = description or tpl.description
        db.session.commit()
        flash('Template saved.', 'success')
        return redirect(url_for('admin.contact_mail_templates'))

    return render_template('admin/contact/mail_template_form.html', tpl=tpl)
