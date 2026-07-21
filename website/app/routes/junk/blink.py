from app.i18n import render_localized_template
from app.routes.junk import junk_bp
from app.routes.junk._ring import ring_nav


@junk_bp.route('/blink')
def blink():
    return render_localized_template('junk/blink.html', **ring_nav('junk.blink'))
