from flask import Blueprint

main_bp = Blueprint('main', __name__)

from app.routes.main import index, about, blog, portfolio  # noqa: E402, F401
