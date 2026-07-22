from flask import render_template
from flask_login import login_required

from app.models.models import (
    BlogCategory, BlogPost, ContactMessage, CvFile, PortfolioProject, Visit,
)
from app.routes.admin import admin_bp


@admin_bp.get('/')
@login_required
def dashboard():
    total_projects = PortfolioProject.query.count()
    total_cvs = CvFile.query.count()
    total_posts = BlogPost.query.count()
    total_categories = BlogCategory.query.count()
    total_messages = ContactMessage.query.count()
    unread_messages = ContactMessage.query.filter_by(is_read=False).count()
    total_visits = Visit.query.count()

    recent_projects = (
        PortfolioProject.query
        .order_by(PortfolioProject.created_at.desc())
        .limit(5).all()
    )
    recent_posts = (
        BlogPost.query
        .order_by(BlogPost.created_at.desc())
        .limit(5).all()
    )
    recent_messages = (
        ContactMessage.query
        .order_by(ContactMessage.created_at.desc())
        .limit(5).all()
    )

    return render_template(
        'admin/dashboard.html',
        total_projects=total_projects,
        total_cvs=total_cvs,
        total_posts=total_posts,
        total_categories=total_categories,
        total_messages=total_messages,
        unread_messages=unread_messages,
        total_visits=total_visits,
        recent_projects=recent_projects,
        recent_posts=recent_posts,
        recent_messages=recent_messages,
    )
