from flask import request

from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/headers')
def headers():
    request_headers = [(name, value) for name, value in request.headers.items()]
    return render_localized_template('nerd/headers.html', request_headers=request_headers)
