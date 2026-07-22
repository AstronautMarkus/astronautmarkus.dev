from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/benchmark')
def benchmark():
    return render_localized_template('nerd/benchmark.html')
