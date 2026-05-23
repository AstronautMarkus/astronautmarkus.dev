from flask import Blueprint

extras_bp = Blueprint('extras', __name__)

from app.routes.extras import pdf_generator  # noqa: E402, F401
