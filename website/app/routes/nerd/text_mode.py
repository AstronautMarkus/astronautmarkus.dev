from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/text-mode')
def text_mode():
    return render_localized_template('nerd/text_mode.html')
