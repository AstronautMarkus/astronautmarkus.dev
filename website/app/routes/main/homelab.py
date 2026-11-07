from app.routes.main import main_bp
from app import render_localized_template

@main_bp.route('/homelab')
def homelab():
    return render_localized_template('main/homelab.html')
