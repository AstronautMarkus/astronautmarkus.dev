from flask import Blueprint

main_bp = Blueprint('main', __name__)

from app.routes.main import index, about, blog, portfolio, proyectadas, profile, gallery, homelab, setup, beercat, guestbook  # noqa: E402, F401
