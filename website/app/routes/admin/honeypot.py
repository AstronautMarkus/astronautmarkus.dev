from datetime import datetime, timedelta

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from app import db
from app.models.models import HoneypotHit
from app.routes.admin import admin_bp

PER_PAGE = 50


@admin_bp.get('/honeypot/')
@login_required
def honeypot_list():
    total = HoneypotHit.query.count()

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)

    today_count = HoneypotHit.query.filter(HoneypotHit.created_at >= today_start).count()
    week_count = HoneypotHit.query.filter(HoneypotHit.created_at >= week_start).count()
    unique_ips = HoneypotHit.query.with_entities(HoneypotHit.ip_address).distinct().count()

    # Last 14 days chart data
    chart_data = []
    max_count = 1
    for i in range(13, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = HoneypotHit.query.filter(
            HoneypotHit.created_at >= day_start,
            HoneypotHit.created_at < day_end,
        ).count()
        chart_data.append({
            'label': day_start.strftime('%m/%d'),
            'count': count,
        })
        if count > max_count:
            max_count = count

    # Most active attacking IPs
    top_ips = (
        HoneypotHit.query
        .with_entities(HoneypotHit.ip_address, db.func.count(HoneypotHit.id).label('hits'))
        .group_by(HoneypotHit.ip_address)
        .order_by(db.desc('hits'))
        .limit(10)
        .all()
    )

    # Filters
    ip_filter = request.args.get('ip', '').strip()
    resource_filter = request.args.get('resource', '').strip()
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    query = HoneypotHit.query.order_by(HoneypotHit.created_at.desc())
    if ip_filter:
        query = query.filter(HoneypotHit.ip_address.contains(ip_filter))
    if resource_filter:
        query = query.filter(HoneypotHit.resource.contains(resource_filter))

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    return render_template(
        'admin/honeypot/list.html',
        total=total,
        today_count=today_count,
        week_count=week_count,
        unique_ips=unique_ips,
        chart_data=chart_data,
        max_count=max_count,
        top_ips=top_ips,
        pagination=pagination,
        ip_filter=ip_filter,
        resource_filter=resource_filter,
    )


@admin_bp.get('/honeypot/<int:hit_id>')
@login_required
def honeypot_detail(hit_id):
    hit = db.session.get(HoneypotHit, hit_id)
    if hit is None:
        flash('Honeypot hit not found.', 'error')
        return redirect(url_for('admin.honeypot_list'))
    return render_template('admin/honeypot/detail.html', hit=hit)


@admin_bp.post('/honeypot/<int:hit_id>/delete')
@login_required
def honeypot_delete(hit_id):
    hit = db.session.get(HoneypotHit, hit_id)
    if hit:
        db.session.delete(hit)
        db.session.commit()
        flash('Honeypot hit deleted.', 'success')
    return redirect(url_for('admin.honeypot_list'))
