from flask import Blueprint

junk_bp = Blueprint('junk', __name__)

from app.routes.junk import (  # noqa: E402, F401
    best_viewed,
    geocities,
    y2k,
    blink,
    marquee,
    dialup,
    under_construction,
    guestbook,
    links,
    webring,
    counter,
)
