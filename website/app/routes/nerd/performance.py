from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/performance')
def performance():
    return render_localized_template('nerd/performance.html')
