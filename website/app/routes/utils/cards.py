import textwrap

from flask import Response, abort, render_template, request
from sqlalchemy import func

from app import db
from app.models.models import BlogPost, GalleryPhoto, GuestbookEntry, PortfolioProject, Visit
from . import utils_bp

# Embeddable SVG cards for READMEs and other sites (listed on /widgets).
# Deliberately neutral (not the site themes) so they sit well on GitHub;
# light/dark comes from prefers-color-scheme inside the SVG.
CARD_WIDTH = 480
BODY_TOP = 48  # header row + gap; card templates draw from here
BODY_PAD = 20
CACHE_SECONDS = 3600
DATE_FORMAT = '%b %d, %Y'


def _wrap(text, width, max_lines):
    # shortcut: wraps by character count, not rendered width; very wide glyphs can overrun the card edge.
    return textwrap.wrap(text or '', width, max_lines=max_lines, placeholder=' …')


def _clip(text, width):
    # For one-liners: textwrap gives up on a single word longer than width (URLs) and returns just the placeholder.
    text = ' '.join((text or '').split())
    return text if len(text) <= width else text[:width - 1].rstrip() + '…'


def _card(template, title, body_height, **context):
    svg = render_template(
        f'cards/{template}',
        title=title,
        width=CARD_WIDTH,
        height=BODY_TOP + body_height + BODY_PAD,
        inner=CARD_WIDTH - 2 * BODY_PAD,
        pad=BODY_PAD,
        top=BODY_TOP,
        host=request.host,
        **context,
    )
    return Response(svg, mimetype='image/svg+xml', headers={'Cache-Control': f'public, max-age={CACHE_SECONDS}'})


def _published_posts():
    return BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc())


@utils_bp.route('/card/stats.svg')
def card_stats():
    stats = [
        (Visit.query.count(), 'visits'),
        (_published_posts().count(), 'blog posts'),
        (db.session.query(func.coalesce(func.sum(BlogPost.view_count), 0))
            .filter(BlogPost.published.is_(True)).scalar(), 'post reads'),
        (PortfolioProject.query.count(), 'projects'),
        (GalleryPhoto.query.count(), 'photos'),
        (GuestbookEntry.query.filter_by(approved=True).count(), 'guestbook signatures'),
    ]
    stats = [(f'{int(value):,}', label) for value, label in stats]
    return _card('stats.svg', 'AstronautMarkus.Dev Stats', 2 * 48 - 10, stats=stats)


@utils_bp.route('/card/latest-post.svg')
def card_latest_post():
    post = _published_posts().first()
    if post is None:
        return _card('empty.svg', 'Latest from the blog', 20, message='No posts yet.')

    title_lines = _wrap(post.title, 46, 2)
    desc_lines = _wrap(post.description, 68, 3)
    meta = ' · '.join(filter(None, [
        post.created_at.strftime(DATE_FORMAT),
        post.category.name if post.category else None,
        f'{post.view_count:,} views',
    ]))
    body_height = len(title_lines) * 20 + 22 + len(desc_lines) * 17
    return _card('latest_post.svg', 'Latest from the blog', body_height,
                 title_lines=title_lines, desc_lines=desc_lines, meta=meta)


@utils_bp.route('/card/posts.svg')
def card_posts():
    posts = [
        (post.created_at.strftime(DATE_FORMAT), _clip(post.title, 54))
        for post in _published_posts().limit(5)
    ]
    if not posts:
        return _card('empty.svg', 'Latest blog posts', 20, message='No posts yet.')
    return _card('posts.svg', 'Latest blog posts', len(posts) * 24, posts=posts)


@utils_bp.route('/card/project/<int:project_id>.svg')
def card_project(project_id):
    project = db.session.get(PortfolioProject, project_id) or abort(404)

    title_lines = _wrap(project.title, 46, 2)
    desc_lines = _wrap(project.description, 68, 3)
    links = [
        (label, _clip(url.split('://', 1)[-1].rstrip('/'), 28))
        for label, url in (('Code', project.github_repo_url), ('Live', project.project_url))
        if url
    ]
    body_height = len(title_lines) * 20 + 6 + len(desc_lines) * 17 + (28 if links else 0)
    return _card('project.svg', 'Portfolio project', body_height,
                 title_lines=title_lines, desc_lines=desc_lines, links=links)


@utils_bp.route('/card/guestbook.svg')
def card_guestbook():
    approved = GuestbookEntry.query.filter_by(approved=True)
    entry = approved.order_by(GuestbookEntry.created_at.desc()).first()
    if entry is None:
        return _card('empty.svg', 'Guest Book', 20, message=f'No signatures yet. Be the first at {request.host}/guestbook')

    message_lines = _wrap(f'“{entry.message}”', 62, 3)
    signed = f'— {_clip(entry.name, 40)}, {entry.created_at.strftime(DATE_FORMAT)}'
    body_height = len(message_lines) * 19 + 22 + 26
    return _card('guestbook.svg', 'Guest Book', body_height,
                 message_lines=message_lines, signed=signed, total=approved.count())
