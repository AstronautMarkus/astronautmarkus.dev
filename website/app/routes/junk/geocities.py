from app.i18n import render_localized_template
from app.routes.junk import junk_bp
from app.routes.junk._ring import ring_nav


@junk_bp.route('/geocities')
def geocities():
    return render_localized_template('junk/geocities.html', **ring_nav('junk.geocities'))
