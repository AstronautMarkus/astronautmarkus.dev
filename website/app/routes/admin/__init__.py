from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.context_processor
def inject_admin_globals():
    try:
        from app.models.models import ContactMessage
        unread = ContactMessage.query.filter_by(is_read=False).count()
    except Exception:
        unread = 0
    return {'admin_unread_contact': unread}


from app.routes.admin import dashboard, projects, cv, blog, contact, visits  # noqa: E402, F401
