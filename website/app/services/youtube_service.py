import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.models import YoutubeVideo

FEED_URL = 'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
REQUEST_TIMEOUT = 15

_NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'yt': 'http://www.youtube.com/xml/schemas/2015',
    'media': 'http://search.yahoo.com/mrss/',
}


class YoutubeSyncError(Exception):
    """Raised when the channel feed could not be fetched or parsed."""


def fetch_feed(channel_id: str) -> list[dict]:
    """Return the channel's latest videos (YouTube's feed holds at most 15)."""
    try:
        response = requests.get(
            FEED_URL.format(channel_id=channel_id),
            timeout=REQUEST_TIMEOUT,
            headers={'User-Agent': 'astronautmarkus.dev youtube-sync'},
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except (requests.RequestException, ET.ParseError) as exc:
        raise YoutubeSyncError(f'Could not read YouTube feed: {exc}') from exc

    videos = []
    for entry in root.findall('atom:entry', _NS):
        video_id = entry.findtext('yt:videoId', namespaces=_NS)
        title = entry.findtext('atom:title', namespaces=_NS)
        published = entry.findtext('atom:published', namespaces=_NS)
        if not (video_id and title and published):
            continue

        stats = entry.find('media:group/media:community/media:statistics', _NS)
        views = stats.get('views', '0') if stats is not None else '0'
        published_at = datetime.fromisoformat(published).astimezone(timezone.utc).replace(tzinfo=None)

        videos.append({
            'video_id': video_id,
            'title': title.strip(),
            'description': (entry.findtext('media:group/media:description', namespaces=_NS) or '').strip(),
            'published_at': published_at,
            'view_count': int(views) if views.isdigit() else 0,
        })
    return videos


def sync_videos() -> dict:
    """Upsert the channel feed into the DB. Videos that fell out of the feed are kept."""
    channel_id = current_app.config['YOUTUBE_CHANNEL_ID']
    if not channel_id:
        raise YoutubeSyncError('YOUTUBE_CHANNEL_ID is not configured')

    feed = fetch_feed(channel_id)
    existing = {
        video.video_id: video
        for video in YoutubeVideo.query.filter(
            YoutubeVideo.video_id.in_([item['video_id'] for item in feed])
        )
    }

    now = datetime.utcnow()
    created = 0
    for item in feed:
        video = existing.get(item['video_id'])
        if video is None:
            db.session.add(YoutubeVideo(**item, synced_at=now))
            created += 1
            continue
        for field, value in item.items():
            setattr(video, field, value)
        video.synced_at = now

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise YoutubeSyncError(f'Could not save videos: {exc}') from exc

    return {'fetched': len(feed), 'created': created}
