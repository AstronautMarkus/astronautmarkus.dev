from flask import abort

from app import db
from app.i18n import render_localized_template
from app.models.models import PortfolioProject
from app.routes.main import main_bp


@main_bp.get('/portfolio/')
def portfolio_list():
    projects = (
        PortfolioProject.query
        .order_by(PortfolioProject.created_at.desc())
        .all()
    )
    return render_localized_template('main/portfolio_list.html', projects=projects)


@main_bp.get('/portfolio/<int:project_id>')
def portfolio_detail(project_id):
    project = db.session.get(PortfolioProject, project_id)
    if project is None:
        abort(404)
    return render_localized_template('main/portfolio_detail.html', project=project)
