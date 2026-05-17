from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models.models import ContactMessage, MailTemplate
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
