from app.routes.main import main_bp
from app import db, render_localized_template
from app.models.models import SyncedSnapshot
from app.i18n import get_current_language
from app.tech_stack import get_tech_stack

@main_bp.route('/about-me')
def about_me():
    return render_localized_template('main/about.html', tech_stack=get_tech_stack(get_current_language()),
                                     github=db.session.get(SyncedSnapshot, 'github'))
