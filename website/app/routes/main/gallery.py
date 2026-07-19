from app.i18n import render_localized_template
from app.models.models import GalleryPhoto
from app.routes.main import main_bp


@main_bp.get('/gallery/')
def gallery_list():
    photos = (
        GalleryPhoto.query
        .order_by(GalleryPhoto.created_at.desc())
        .all()
    )
    return render_localized_template('main/gallery_list.html', photos=photos)
