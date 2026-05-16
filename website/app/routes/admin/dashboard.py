from flask import render_template
from flask_login import login_required

from app.models.models import CvFile, PortfolioProject
from app.routes.admin import admin_bp


@admin_bp.get('/')
@login_required
def dashboard():
    total_projects = PortfolioProject.query.count()
    total_cvs = CvFile.query.count()
    recent = (
        PortfolioProject.query
        .order_by(PortfolioProject.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        'admin/dashboard.html',
        total_projects=total_projects,
        total_cvs=total_cvs,
        recent_projects=recent,
    )
