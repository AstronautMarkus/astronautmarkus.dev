from app.routes.main import main_bp
from app import render_localized_template

@main_bp.route('/about-me')
def about_me():
    return render_localized_template('main/about.html')
