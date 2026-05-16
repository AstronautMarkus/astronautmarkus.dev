from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from app.routes.admin import dashboard, projects, cv, blog  # noqa: E402, F401
