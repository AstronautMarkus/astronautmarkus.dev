import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from flask import abort, current_app, render_template, request, url_for
from markupsafe import escape

from app import db
from app.i18n import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    get_current_language,
    render_localized_template,
)
from app.models.models import BlogCategory, BlogPost, BlogPostView, BlogTag
from app.routes.main import main_bp
from app.storage import storage
from app.utils import expand_media_shorthand, render_markdown


def _register_post_view(post: BlogPost) -> None:
    """Increment post.view_count, deduped per IP within a rolling window (mirrors the site-wide Visit pattern)."""
    ip_address = request.remote_addr
    if not ip_address:
        return

    last_view = (
        BlogPostView.query
        .filter_by(post_id=post.id, ip_address=ip_address)
        .order_by(BlogPostView.viewed_at.desc())
        .first()
    )

    if last_view and last_view.viewed_at:
        elapsed = current_app.config.get('POST_VIEW_REGISTER_INTERVAL_HOURS', 24)
        cutoff = datetime.utcnow() - timedelta(hours=elapsed)
        if last_view.viewed_at > cutoff:
            return

    try:
        db.session.add(BlogPostView(post_id=post.id, ip_address=ip_address))
        post.view_count = (post.view_count or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()


def _localized_fields(post: BlogPost, lang: str) -> tuple[str, str | None, str | None]:
    """Return (title, description, markdown_path) in `lang`, falling back to English when the post has no Spanish version."""
    if lang == 'es' and post.has_es:
        return (
            post.title_es or post.title,
            post.description_es or post.description,
            post.markdown_path_es or post.markdown_path,
        )
    return post.title, post.description, post.markdown_path


def _render_post_content(post: BlogPost, md_path: str | None):
    if not md_path or not storage.exists(md_path):
        return None
    raw = storage.get(md_path)
    if not raw:
        return None
    text = expand_media_shorthand(raw.decode('utf-8'), f'blog/posts/{post.slug}/images')
    return render_markdown(text)


@main_bp.get('/blog/')
def blog_list():
    page       = request.args.get('page', 1, type=int)
    cat_id     = request.args.get('cat', None, type=int)
    tag_id     = request.args.get('tag', None, type=int)
    per_page   = 8

    q = BlogPost.query.filter_by(published=True)
    if cat_id:
        q = q.filter_by(category_id=cat_id)
    if tag_id:
        q = q.filter(BlogPost.tags.any(BlogTag.id == tag_id))

    pagination = (
        q.order_by(BlogPost.created_at.desc())
         .paginate(page=page, per_page=per_page, error_out=False)
    )

    categories = BlogCategory.query.order_by(BlogCategory.name).all()

    return render_localized_template(
        'main/blog_list.html',
        pagination=pagination,
        posts=pagination.items,
        categories=categories,
        current_cat=cat_id,
        current_tag=tag_id,
        current_category=None,
        pagination_endpoint='main.blog_list',
        pagination_kwargs={'cat': cat_id, 'tag': tag_id},
    )


@main_bp.get('/blog/category/<slug>')
def blog_category_detail(slug):
    category = BlogCategory.query.filter_by(slug=slug).first_or_404()
    page      = request.args.get('page', 1, type=int)
    per_page  = 8

    pagination = (
        BlogPost.query
        .filter_by(published=True, category_id=category.id)
        .order_by(BlogPost.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    categories = BlogCategory.query.order_by(BlogCategory.name).all()

    return render_localized_template(
        'main/blog_list.html',
        pagination=pagination,
        posts=pagination.items,
        categories=categories,
        current_cat=category.id,
        current_tag=None,
        current_category=category,
        pagination_endpoint='main.blog_category_detail',
        pagination_kwargs={'slug': category.slug},
    )


RSS_ITEM_LIMIT = 20

# Root-relative src/href (like the /media/... URLs from expand_media_shorthand)
# mean nothing outside the site, so they're made absolute for feed readers.
_ROOT_RELATIVE_URL = re.compile(r'''(\b(?:src|href)=["'])/(?!/)''')


@main_bp.get('/blog/rss.xml')
def blog_rss():
    # Language comes only from ?lang=, never the cookie or Accept-Language,
    # so FeedBurner and feed readers always get the same feed for the same URL.
    lang = request.args.get('lang', DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    site_root = request.url_root.rstrip('/')
    # Links go through /<lang>/..., which sets the language cookie and redirects
    # (see redirect_lang_prefix), so readers land on the post in the feed's language.
    lang_root = f'{site_root}/{lang}'

    posts = (
        BlogPost.query
        .filter_by(published=True)
        .order_by(BlogPost.created_at.desc())
        .limit(RSS_ITEM_LIMIT)
        .all()
    )

    items = []
    for post in posts:
        title, description, md_path = _localized_fields(post, lang)

        # Plain str, not Markup, so the .xml template's autoescape encodes the HTML.
        content_html = str(_render_post_content(post, md_path) or '')
        content_html = _ROOT_RELATIVE_URL.sub(lambda m: f'{m.group(1)}{site_root}/', content_html)

        cover_url = None
        if post.cover_image_path:
            # /media/ rather than storage_url(): S3 presigned URLs expire, feed copies don't.
            cover_url = url_for('serve_media', file_path=post.cover_image_path, _external=True)
            content_html = f'<p><img src="{escape(cover_url)}" alt="{escape(title)}"></p>{content_html}'

        categories = []
        if post.category:
            use_es = lang == 'es' and post.category.has_es and post.category.name_es
            categories.append(post.category.name_es if use_es else post.category.name)
        categories.extend(tag.name for tag in post.tags)

        items.append({
            'title': title,
            'link': lang_root + url_for('main.blog_post_detail', slug=post.slug),
            'description': description,
            # created_at is naive; treated as UTC.
            'pub_date': format_datetime(post.created_at.replace(tzinfo=timezone.utc), usegmt=True),
            'categories': categories,
            'cover_url': cover_url,
            'content_html': content_html,
        })

    xml = render_template(
        'main/blog_rss.xml',
        lang=lang,
        items=items,
        last_build_date=items[0]['pub_date'] if items else None,
        channel_link=lang_root + url_for('main.blog_list'),
        self_url=url_for('main.blog_rss', lang=None if lang == DEFAULT_LANGUAGE else lang, _external=True),
    )
    response = current_app.response_class(xml, mimetype='application/rss+xml')
    response.add_etag()
    return response.make_conditional(request)


@main_bp.get('/blog/<slug>')
def blog_post_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()

    _register_post_view(post)

    title, description, md_path = _localized_fields(post, get_current_language())
    content_html = _render_post_content(post, md_path)

    return render_localized_template(
        'main/blog_post.html',
        post=post,
        title=title,
        description=description,
        content_html=content_html,
    )
