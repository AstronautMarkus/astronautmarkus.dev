from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/carbon-footprint')
def carbon_footprint():
    return render_localized_template('nerd/carbon_footprint.html')
