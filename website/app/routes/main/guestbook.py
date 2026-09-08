import time

from flask import current_app, flash, redirect, request, url_for

from app import db
from app.i18n import render_localized_template
from app.models.models import GuestbookEntry
from app.routes.main import main_bp

# ─── Anti-spam ─────────────────────────────────────────────────────────────────

HONEYPOT_FIELD = 'company_site'  # decoy field — real users never see or fill it
MIN_SUBMIT_SECONDS = 3           # forms submitted faster than this are treated as bots

PER_PAGE = 20
NAME_MAX_LEN = 100
MESSAGE_MAX_LEN = 1000


def _render(form_data, field_errors, form_ts):
    page = max(request.args.get('page', 1, type=int), 1)
    pagination = GuestbookEntry.query.filter_by(approved=True).order_by(
        GuestbookEntry.created_at.desc()
    ).paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_localized_template(
        'main/guestbook.html',
        entries=pagination.items,
        pagination=pagination,
        form_data=form_data,
        field_errors=field_errors,
        form_ts=form_ts,
    )


@main_bp.route('/guestbook', methods=['GET', 'POST'])
def guestbook():
    if request.method == 'POST':
        ip = request.remote_addr

        # Honeypot — a hidden field real visitors never fill. Pretend success so bots don't adapt.
        if request.form.get(HONEYPOT_FIELD, '').strip():
            current_app.logger.warning('Guestbook: honeypot triggered from ip=%s', ip)
            flash('signed', 'success')
            return redirect(url_for('main.guestbook'))

        # Timing trap — forms submitted faster than a human can fill are almost certainly scripted.
        try:
            rendered_at = float(request.form.get('form_ts', ''))
        except ValueError:
            rendered_at = 0.0
        if rendered_at and (time.time() - rendered_at) < MIN_SUBMIT_SECONDS:
            current_app.logger.warning('Guestbook: submitted too fast from ip=%s', ip)
            flash('signed', 'success')
            return redirect(url_for('main.guestbook'))

        name = request.form.get('name', '').strip()[:NAME_MAX_LEN]
        message = request.form.get('message', '').strip()[:MESSAGE_MAX_LEN]
        form_data = {'name': name, 'message': message}

        field_errors: list[str] = []
        if not name:
            field_errors.append('name')
        if not message:
            field_errors.append('message')

        if field_errors:
            flash('validation_error', 'error')
            return _render(form_data, field_errors, time.time())

        db.session.add(GuestbookEntry(name=name, message=message, ip_address=ip))
        db.session.commit()

        flash('signed', 'success')
        return redirect(url_for('main.guestbook'))

    return _render({}, [], time.time())
