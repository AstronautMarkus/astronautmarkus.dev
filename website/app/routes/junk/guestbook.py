import time

from flask import flash, redirect, request, url_for

from app import db
from app.i18n import get_current_language, render_localized_template
from app.models.models import GuestbookEntry
from app.routes.junk import junk_bp
from app.routes.junk._ring import ring_nav

HONEYPOT_FIELD = 'homepage_url'  # decoy field — real visitors never see or fill it
MIN_SUBMIT_SECONDS = 3           # entries submitted faster than this are treated as bots


@junk_bp.route('/guestbook', methods=['GET', 'POST'])
def guestbook():
    lang = get_current_language()

    if request.method == 'POST':
        ip = request.remote_addr
        name = request.form.get('name', '').strip()
        message = request.form.get('message', '').strip()

        # Honeypot — pretend success so bots don't adapt.
        if request.form.get(HONEYPOT_FIELD, '').strip():
            flash('sent', 'success')
            return redirect(url_for('junk.guestbook'))

        # Timing trap — forms submitted faster than a human can fill are almost certainly scripted.
        try:
            rendered_at = float(request.form.get('form_ts', ''))
        except ValueError:
            rendered_at = 0.0
        if rendered_at and (time.time() - rendered_at) < MIN_SUBMIT_SECONDS:
            flash('sent', 'success')
            return redirect(url_for('junk.guestbook'))

        if not name or not message:
            flash('validation_error', 'error')
            return redirect(url_for('junk.guestbook'))

        entry = GuestbookEntry(name=name[:100], message=message, ip_address=ip)
        db.session.add(entry)
        db.session.commit()

        flash('sent', 'success')
        return redirect(url_for('junk.guestbook'))

    entries = (
        GuestbookEntry.query
        .filter_by(approved=True)
        .order_by(GuestbookEntry.created_at.desc())
        .all()
    )
    return render_localized_template(
        'junk/guestbook.html',
        entries=entries,
        form_ts=time.time(),
        **ring_nav('junk.guestbook'),
    )
