import os
from datetime import date

from flask import current_app

from app.routes.main import main_bp
from app.i18n import render_localized_template
from app.theme_schedule import today
from app import db
from app.models.models import BlogPost, BlogTag, PortfolioProject, Proyectada, SyncedSnapshot, Visit

PAYDAY_SCREENSHOTS_DIR = 'images/home/payday-bank'
PAYDAY_SCREENSHOT_EXTS = ('.png', '.jpg', '.jpeg', '.webp')
CODING_SINCE = 2022
CAFFEINE_SINCE = date(2020, 1, 1)
COFFEE_PER_DAY = 4.5  # 4-5 cups a day
MONSTERS_PER_DAY = 0.5  # guess: one can every other day


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
    caffeine_days = (today() - CAFFEINE_SINCE).days

    return render_localized_template(
        'main/home.html',
        projects=projects,
        latest_posts=latest_posts,
        latest_proyectadas=latest_proyectadas,
        all_tags=all_tags,
        total_visits=total_visits,
        years_coding=today().year - CODING_SINCE,
        coffee_cups=int(caffeine_days * COFFEE_PER_DAY),
        monster_cans=int(caffeine_days * MONSTERS_PER_DAY),
        payday_screenshots=_payday_screenshots(),
        github=db.session.get(SyncedSnapshot, 'github'),
        payday_screenshots_dir=PAYDAY_SCREENSHOTS_DIR,
    )
