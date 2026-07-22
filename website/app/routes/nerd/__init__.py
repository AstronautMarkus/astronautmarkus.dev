from flask import Blueprint

nerd_bp = Blueprint('nerd', __name__)

from app.routes.nerd import (  # noqa: E402, F401
    performance,
    lighthouse,
    metrics,
    size,
    payload,
    headers,
    response_time,
    benchmark,
    carbon_footprint,
    no_js,
    no_css,
    html_only,
    text_mode,
)
