from app.i18n import render_localized_template
from app.routes.junk import junk_bp


@junk_bp.route('/webring')
def webring():
    return render_localized_template('junk/webring.html')
