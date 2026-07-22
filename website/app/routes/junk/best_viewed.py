from app.i18n import render_localized_template
from app.routes.junk import junk_bp
from app.routes.junk._ring import ring_nav


@junk_bp.route('/best-viewed-800x600')
def best_viewed():
    return render_localized_template('junk/best_viewed.html', **ring_nav('junk.best_viewed'))
