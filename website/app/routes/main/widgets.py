from app.routes.main import main_bp
from app import render_localized_template
from app.models.models import PortfolioProject


@main_bp.route('/widgets')
def widgets():
    projects = PortfolioProject.query.order_by(PortfolioProject.created_at.desc()).all()
    return render_localized_template('main/widgets.html', projects=projects)
