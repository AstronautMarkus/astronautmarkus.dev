import gzip

from flask import request

from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/payload')
def payload():
    ctx = {
        'raw_bytes': 0,
        'gzip_bytes': 0,
        'savings_pct': 0,
        'content_type': 'text/html; charset=utf-8',
        'method': request.method,
        'is_secure': request.is_secure,
    }
    html = render_localized_template('nerd/payload.html', **ctx)

    raw_bytes = len(html.encode('utf-8'))
    gzip_bytes = len(gzip.compress(html.encode('utf-8')))
    savings_pct = round((1 - gzip_bytes / raw_bytes) * 100, 1) if raw_bytes else 0

    ctx.update(raw_bytes=raw_bytes, gzip_bytes=gzip_bytes, savings_pct=savings_pct)
    return render_localized_template('nerd/payload.html', **ctx)
