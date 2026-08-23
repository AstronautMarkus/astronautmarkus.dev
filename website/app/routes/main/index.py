import os

from flask import current_app

from app.routes.main import main_bp
from app.i18n import render_localized_template
from app.models.models import BlogPost, BlogTag, PortfolioProject, Proyectada, Visit

PAYDAY_SCREENSHOTS_DIR = 'images/home/payday-bank'
PAYDAY_SCREENSHOT_EXTS = ('.png', '.jpg', '.jpeg', '.webp')


def _payday_screenshots():
    folder = os.path.join(current_app.static_folder, *PAYDAY_SCREENSHOTS_DIR.split('/'))
    if not os.path.isdir(folder):
        return []
    return sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(PAYDAY_SCREENSHOT_EXTS)
    )


@main_bp.route('/')
def home():
    projects = (
        PortfolioProject.query
        .order_by(PortfolioProject.created_at.desc())
        .limit(4)
        .all()
    )

    latest_posts = (
        BlogPost.query
        .filter_by(published=True)
        .order_by(BlogPost.created_at.desc())
        .limit(4)
        .all()
    )

    latest_proyectadas = (
        Proyectada.query
        .filter_by(published=True)
        .order_by(Proyectada.created_at.desc())
        .limit(3)
        .all()
    )

    all_tags = BlogTag.query.order_by(BlogTag.name).all()
    total_visits = Visit.query.count()

    return render_localized_template(
        'main/home.html',
        projects=projects,
        latest_posts=latest_posts,
        latest_proyectadas=latest_proyectadas,
        all_tags=all_tags,
        total_visits=total_visits,
        payday_screenshots=_payday_screenshots(),
        payday_screenshots_dir=PAYDAY_SCREENSHOTS_DIR,
    )
