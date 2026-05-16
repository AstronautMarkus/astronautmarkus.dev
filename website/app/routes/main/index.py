from flask import url_for
from app.routes.main import main_bp
from app.i18n import get_current_language, render_localized_template
from app.models.models import BlogPost, CvFile, PortfolioProject


@main_bp.route('/')
def home():
    lang = get_current_language()

    cv = CvFile.query.filter_by(language=lang).order_by(CvFile.uploaded_at.desc()).first()
    cv_url = url_for('serve_media', file_path=cv.file_path) if cv else None

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

    return render_localized_template('main/home.html', cv_url=cv_url, projects=projects, latest_posts=latest_posts)
