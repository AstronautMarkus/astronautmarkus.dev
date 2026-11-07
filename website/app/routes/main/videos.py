from flask import current_app

from app.i18n import render_localized_template
from app.models.models import YoutubeVideo
from app.routes.main import main_bp


@main_bp.get('/videos/')
def videos_list():
    videos = (
        YoutubeVideo.query
        .order_by(YoutubeVideo.published_at.desc())
        .all()
    )
    return render_localized_template(
        'main/videos.html',
        featured=videos[0] if videos else None,
        videos=videos[1:],
        channel_url=current_app.config['YOUTUBE_CHANNEL_URL'],
    )
