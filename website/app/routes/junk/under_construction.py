from app.i18n import render_localized_template
from app.routes.junk import junk_bp
from app.routes.junk._ring import ring_nav


@junk_bp.route('/under-construction')
def under_construction():
    return render_localized_template('junk/under_construction.html', **ring_nav('junk.under_construction'))
