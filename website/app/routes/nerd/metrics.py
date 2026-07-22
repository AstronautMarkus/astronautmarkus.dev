from app.i18n import render_localized_template
from app.models.models import BlogPost, GalleryPhoto, GuestbookEntry, PortfolioProject, Visit
from app.routes.nerd import nerd_bp


@nerd_bp.route('/metrics')
def metrics():
    stats = {
        'visits': Visit.query.count(),
        'guestbook_entries': GuestbookEntry.query.filter_by(approved=True).count(),
        'blog_posts': BlogPost.query.filter_by(published=True).count(),
        'portfolio_projects': PortfolioProject.query.count(),
        'gallery_photos': GalleryPhoto.query.count(),
    }
    return render_localized_template('nerd/metrics.html', stats=stats)
