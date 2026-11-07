from datetime import date

from app.routes.main import main_bp
from app.i18n import render_localized_template
from app.theme_schedule import today
from app import db
from app.models.models import BlogPost, BlogTag, PortfolioProject, Proyectada, SyncedSnapshot, Visit

PAYDAY_SCREENSHOTS_DIR = 'images/home/payday-bank'
# Served from the CDN (see cdn_url), so they're listed here instead of read from static/
PAYDAY_SCREENSHOTS = (
    'payday-bank-01-dashboard.webp',
    'payday-bank-02-landing.webp',
    'payday-bank-03-architecture.webp',
    'payday-bank-04-accounts.webp',
    'payday-bank-05-statement.webp',
    'payday-bank-06-transfers.webp',
    'payday-bank-07-cards.webp',
    'payday-bank-08-card-payment.webp',
    'payday-bank-09-login.webp',
    'payday-bank-10-sign-up.webp',
)
CODING_SINCE = 2022
CAFFEINE_SINCE = date(2020, 1, 1)
COFFEE_PER_DAY = 4.5  # 4-5 cups a day
MONSTERS_PER_DAY = 0.5  # guess: one can every other day


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
        payday_screenshots=PAYDAY_SCREENSHOTS,
        github=db.session.get(SyncedSnapshot, 'github'),
        payday_screenshots_dir=PAYDAY_SCREENSHOTS_DIR,
    )
