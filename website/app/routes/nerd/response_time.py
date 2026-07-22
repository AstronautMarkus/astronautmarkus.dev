import time

from app.i18n import render_localized_template
from app.models.models import Visit
from app.routes.nerd import nerd_bp


@nerd_bp.route('/response-time')
def response_time():
    query_start = time.perf_counter()
    Visit.query.count()
    query_ms = round((time.perf_counter() - query_start) * 1000, 2)

    render_start = time.perf_counter()
    render_localized_template('nerd/response_time.html', render_ms=0, query_ms=query_ms)
    render_ms = round((time.perf_counter() - render_start) * 1000, 2)

    return render_localized_template('nerd/response_time.html', render_ms=render_ms, query_ms=query_ms)
