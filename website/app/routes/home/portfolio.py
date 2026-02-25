from flask import render_template
from . import home_bp
from app.models.models import PortfolioProject, ProjectTechTag

@home_bp.route('/portfolio')
def portfolio():
    projects = PortfolioProject.query.order_by(PortfolioProject.id.desc()).all()
    return render_template('portfolio.html', projects=projects)
