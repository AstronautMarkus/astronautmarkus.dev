from datetime import datetime, timedelta

from flask import abort, current_app, request

from app import db
from app.i18n import get_current_language, render_localized_template
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


@main_bp.get('/blog/<slug>')
def blog_post_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    lang = get_current_language()

    _register_post_view(post)

    use_es      = lang == 'es' and post.has_es
    title       = (post.title_es or post.title)       if use_es else post.title
    description = (post.description_es or post.description) if use_es else post.description
    md_path     = (post.markdown_path_es or post.markdown_path) if use_es else post.markdown_path

    content_html = None
    if md_path and storage.exists(md_path):
        raw = storage.get(md_path)
        if raw:
            text = expand_media_shorthand(raw.decode('utf-8'), f'blog/posts/{post.slug}/images')
            content_html = render_markdown(text)

    return render_localized_template(
        'main/blog_post.html',
        post=post,
        title=title,
        description=description,
        content_html=content_html,
    )
