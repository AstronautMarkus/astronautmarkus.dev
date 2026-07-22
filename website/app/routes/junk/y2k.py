from app.i18n import render_localized_template
from app.routes.junk import junk_bp
from app.routes.junk._ring import ring_nav


@junk_bp.route('/y2k')
def y2k():
    return render_localized_template('junk/y2k.html', **ring_nav('junk.y2k'))
