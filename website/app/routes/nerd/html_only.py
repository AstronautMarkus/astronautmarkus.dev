from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/html-only')
def html_only():
    # Standalone for the same reason as /no-css — and this template also
    # avoids <div>/class entirely, using only semantic elements.
    return render_localized_template('nerd/html_only.html')
