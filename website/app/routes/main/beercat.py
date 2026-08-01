from app.routes.main import main_bp
from app import render_localized_template


@main_bp.route('/beercat')
def beercat():
    return render_localized_template('main/beercat.html')
