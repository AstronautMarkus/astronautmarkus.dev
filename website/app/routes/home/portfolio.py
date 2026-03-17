from flask import render_template
from . import home_bp
from app.models.models import PortfolioProject


PORTFOLIO_GROUP_ORDER = ['professional', 'personal', 'community']


def _get_grouped_projects():
    projects = PortfolioProject.query.order_by(PortfolioProject.id.desc()).all()
    grouped_projects = {group: [] for group in PORTFOLIO_GROUP_ORDER}

    for project in projects:
        if project.project_type in grouped_projects:
            grouped_projects[project.project_type].append(project)

    return grouped_projects

@home_bp.route('/portfolio')
def portfolio():
    grouped_projects = _get_grouped_projects()
    return render_template('/home/portfolio.html', grouped_projects=grouped_projects)

@home_bp.route('/es/portfolio')
def portfolio_es():
    grouped_projects = _get_grouped_projects()
    return render_template('/home/es/portfolio.html', grouped_projects=grouped_projects)