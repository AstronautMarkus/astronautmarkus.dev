from app.routes.main import main_bp
from app import render_localized_template


@main_bp.route('/about')
def about():
    return render_localized_template('about.html')
