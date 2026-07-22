from flask import Blueprint

contact_bp = Blueprint('contact', __name__)

from app.routes.contact import contact  # noqa: E402, F401
