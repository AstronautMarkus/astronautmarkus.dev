from datetime import datetime, timedelta

from flask import render_template, request
from flask_login import login_required

from app.models.models import Visit
from app.routes.admin import admin_bp

PER_PAGE = 50


@admin_bp.get('/visits/')
@login_required
def visits_list():
    total = Visit.query.count()

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)

    today_count = Visit.query.filter(Visit.visited_at >= today_start).count()
    week_count = Visit.query.filter(Visit.visited_at >= week_start).count()

    # Last 14 days chart data
    chart_data = []
    max_count = 1
    for i in range(13, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = Visit.query.filter(
            Visit.visited_at >= day_start,
            Visit.visited_at < day_end,
        ).count()
        chart_data.append({
            'label': day_start.strftime('%m/%d'),
            'count': count,
        })
        if count > max_count:
            max_count = count

    # Filters
    ip_filter = request.args.get('ip', '').strip()
    utm_filter = request.args.get('utm', '').strip()
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    query = Visit.query.order_by(Visit.visited_at.desc())
    if ip_filter:
        query = query.filter(Visit.ip_address.contains(ip_filter))
    if utm_filter:
        query = query.filter(Visit.utm_source.contains(utm_filter))

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    return render_template(
        'admin/visits.html',
        total=total,
        today_count=today_count,
        week_count=week_count,
        chart_data=chart_data,
        max_count=max_count,
        pagination=pagination,
        ip_filter=ip_filter,
        utm_filter=utm_filter,
    )
