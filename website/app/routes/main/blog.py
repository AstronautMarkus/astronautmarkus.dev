from flask import abort, render_template, request

from app.i18n import get_current_language
from app.models.models import BlogCategory, BlogPost
from app.routes.main import main_bp
from app.storage import storage
from app.utils import expand_post_images, render_markdown


@main_bp.get('/blog/')
def blog_list():
    page       = request.args.get('page', 1, type=int)
    cat_id     = request.args.get('cat', None, type=int)
    per_page   = 8

    q = BlogPost.query.filter_by(published=True)
    if cat_id:
        q = q.filter_by(category_id=cat_id)

    pagination = (
        q.order_by(BlogPost.created_at.desc())
         .paginate(page=page, per_page=per_page, error_out=False)
    )

    categories = BlogCategory.query.order_by(BlogCategory.name).all()

    return render_template(
        'main/blog_list.html',
        pagination=pagination,
        posts=pagination.items,
        categories=categories,
        current_cat=cat_id,
    )


@main_bp.get('/blog/<slug>')
def blog_post_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    lang = get_current_language()

    use_es      = lang == 'es' and post.has_es
    title       = (post.title_es or post.title)       if use_es else post.title
    description = (post.description_es or post.description) if use_es else post.description
    md_path     = (post.markdown_path_es or post.markdown_path) if use_es else post.markdown_path

    content_html = None
    if md_path and storage.exists(md_path):
        raw = storage.get(md_path)
        if raw:
            text = expand_post_images(raw.decode('utf-8'), post.slug)
            content_html = render_markdown(text)

    return render_template(
        'main/blog_post.html',
        post=post,
        title=title,
        description=description,
        content_html=content_html,
    )
