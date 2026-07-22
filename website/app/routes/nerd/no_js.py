from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/no-js')
def no_js():
    return render_localized_template('nerd/no_js.html')
