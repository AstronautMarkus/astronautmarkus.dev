from app.routes.main import main_bp
from app import render_localized_template

@main_bp.route('/setup')
def setup():
    return render_localized_template('main/setup.html')
