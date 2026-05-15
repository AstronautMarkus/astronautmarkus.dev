from app.routes.main import main_bp
from app import render_localized_template

@main_bp.route('/')
def home():
    return render_localized_template('main/home.html')
