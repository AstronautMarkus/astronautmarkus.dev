import re
from datetime import datetime

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.i18n import t
from app.models.models import BlogCategory, BlogPost, BlogPostImage, BlogTag
from app.routes.admin import admin_bp
from app.services.ai_service import AIServiceError, is_enabled, suggest_blog_metadata
from app.storage import storage

ALLOWED_MD  = {'md', 'markdown'}
ALLOWED_IMG = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
MAX_MD_BYTES  = 2 * 1024 * 1024   # 2 MB
MAX_IMG_BYTES = 5 * 1024 * 1024   # 5 MB
PER_PAGE = 50


def _allowed_md(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_MD


def _allowed_img(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMG


def _store_md(file, dest_path: str) -> bool:
    """Validate and persist an uploaded Markdown file. Returns True on success."""
    if not file or not file.filename:
        return False
    if not _allowed_md(file.filename):
        return False
    content = file.read()
    if len(content) > MAX_MD_BYTES:
        return False
    storage.put(dest_path, content, content_type='text/markdown; charset=utf-8')
    return True


def _store_img(file, dest_path: str) -> bool:
    """Validate and persist an uploaded image file. Returns True on success."""
    if not file or not file.filename:
        return False
    if not _allowed_img(file.filename):
        return False
    content = file.read()
    if len(content) > MAX_IMG_BYTES:
        return False
    storage.put(dest_path, content, content_type=file.content_type or 'image/jpeg')
    return True


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-{2,}', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text or 'post'


def _parse_tags(raw: str) -> list[BlogTag]:
    """Parse a comma-separated tag string, returning existing or newly created BlogTags."""
    seen = set()
    tags = []
    for part in raw.split(','):
        name = part.strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        tag = BlogTag.query.filter(db.func.lower(BlogTag.name) == key).first()
        if not tag:
            tag = BlogTag(name=name)
            db.session.add(tag)
            db.session.flush()
        tags.append(tag)
    return tags


def _unique_slug(model, base: str, exclude_id: int | None = None) -> str:
    slug = base
    i = 2
    while True:
        q = model.query.filter_by(slug=slug)
        if exclude_id:
            q = q.filter(model.id != exclude_id)
        if not q.first():
            return slug
        slug = f'{base}-{i}'
        i += 1


# ══ Categories ════════════════════════════════════════════════════════════════

@admin_bp.get('/blog/categories/')
@login_required
def blog_categories_list():
    page = max(request.args.get('page', 1, type=int), 1)
    pagination = BlogCategory.query.order_by(BlogCategory.name).paginate(
        page=page, per_page=PER_PAGE, error_out=False
    )
    return render_template('admin/blog/category_list.html', pagination=pagination, categories=pagination.items)


@admin_bp.route('/blog/categories/create', methods=['GET', 'POST'])
@login_required
def blog_category_create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash(t('flash.category_name_required'), 'error')
            return render_template('admin/blog/category_form.html', category=None)

        has_es = request.form.get('has_es') == '1'
        name_es = request.form.get('name_es', '').strip() or None
        slug_input = request.form.get('slug', '').strip()
        base_slug = _slugify(slug_input) if slug_input else _slugify(name)

        cat = BlogCategory(
            name=name,
            has_es=has_es,
            name_es=name_es if has_es else None,
            slug='__tmp__',
        )
        db.session.add(cat)
        db.session.flush()

        cat.slug = _unique_slug(BlogCategory, base_slug, exclude_id=cat.id)

        db.session.commit()
        flash(t('flash.category_created', name=cat.name), 'success')
        return redirect(url_for('admin.blog_categories_list'))

    return render_template('admin/blog/category_form.html', category=None)


@admin_bp.route('/blog/categories/<int:cat_id>/edit', methods=['GET', 'POST'])
@login_required
def blog_category_edit(cat_id):
    category = db.session.get(BlogCategory, cat_id)
    if category is None:
        flash(t('flash.category_not_found'), 'error')
        return redirect(url_for('admin.blog_categories_list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash(t('flash.category_name_required'), 'error')
            return render_template('admin/blog/category_form.html', category=category)

        has_es = request.form.get('has_es') == '1'
        name_es = request.form.get('name_es', '').strip() or None

        category.name = name
        category.has_es = has_es
        category.name_es = name_es if has_es else None
        db.session.commit()
        flash(t('flash.category_updated'), 'success')
        return redirect(url_for('admin.blog_category_edit', cat_id=category.id))

    return render_template('admin/blog/category_form.html', category=category)


@admin_bp.post('/blog/categories/<int:cat_id>/delete')
@login_required
def blog_category_delete(cat_id):
    category = db.session.get(BlogCategory, cat_id)
    if category is None:
        flash(t('flash.category_not_found'), 'error')
        return redirect(url_for('admin.blog_categories_list'))

    if category.posts:
        flash(t('flash.category_in_use', name=category.name, n=len(category.posts)), 'error')
        return redirect(url_for('admin.blog_categories_list'))

    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(t('flash.category_deleted', name=name), 'success')
    return redirect(url_for('admin.blog_categories_list'))


# ══ Posts ══════════════════════════════════════════════════════════════════════

@admin_bp.get('/blog/')
@login_required
def blog_posts_list():
    q = request.args.get('q', '').strip()
    page = max(request.args.get('page', 1, type=int), 1)

    query = BlogPost.query.order_by(BlogPost.created_at.desc())
    if q:
        query = query.filter(BlogPost.title.contains(q))

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template('admin/blog/post_list.html', pagination=pagination, posts=pagination.items, q=q)


@admin_bp.route('/blog/create', methods=['GET', 'POST'])
@login_required
def blog_post_create():
    categories = BlogCategory.query.order_by(BlogCategory.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash(t('flash.title_required'), 'error')
            return render_template('admin/blog/post_form.html', post=None, categories=categories,
                                   now_dt=datetime.utcnow().strftime('%Y-%m-%dT%H:%M'), ai_enabled=is_enabled())

        has_es      = request.form.get('has_es') == '1'
        published   = request.form.get('published') == '1'
        category_id = request.form.get('category_id') or None
        slug_input  = request.form.get('slug', '').strip()
        base_slug   = _slugify(slug_input) if slug_input else _slugify(title)

        created_at_raw = request.form.get('created_at', '').strip()
        try:
            created_at = datetime.strptime(created_at_raw, '%Y-%m-%dT%H:%M') if created_at_raw else datetime.utcnow()
        except ValueError:
            created_at = datetime.utcnow()

        post = BlogPost(
            title=title,
            description=request.form.get('description', '').strip() or None,
            has_es=has_es,
            title_es=request.form.get('title_es', '').strip() or None if has_es else None,
            description_es=request.form.get('description_es', '').strip() or None if has_es else None,
            category_id=int(category_id) if category_id else None,
            published=published,
            slug='__tmp__',
            created_at=created_at,
        )
        post.tags = _parse_tags(request.form.get('tags', ''))

        db.session.add(post)
        db.session.flush()

        post.slug = _unique_slug(BlogPost, base_slug, exclude_id=post.id)

        # Cover image
        cover = request.files.get('cover_image')
        if cover and cover.filename:
            ext = secure_filename(cover.filename).rsplit('.', 1)[-1].lower()
            cover_path = f'blog/posts/{post.slug}/cover.{ext}'
            if _store_img(cover, cover_path):
                post.cover_image_path = cover_path
            else:
                flash(t('flash.cover_rejected'), 'error')

        # Markdown EN
        md_en = request.files.get('markdown_file')
        if md_en and md_en.filename:
            path_en = f'blog/posts/{post.slug}/content_en.md'
            if _store_md(md_en, path_en):
                post.markdown_path = path_en
            else:
                flash(t('flash.en_md_rejected'), 'error')

        # Markdown ES
        if has_es:
            md_es = request.files.get('markdown_file_es')
            if md_es and md_es.filename:
                path_es = f'blog/posts/{post.slug}/content_es.md'
                if _store_md(md_es, path_es):
                    post.markdown_path_es = path_es
                else:
                    flash(t('flash.es_md_rejected'), 'error')

        db.session.commit()
        flash(t('flash.post_created', title=post.title), 'success')
        return redirect(url_for('admin.blog_post_edit', post_id=post.id))

    return render_template('admin/blog/post_form.html', post=None, categories=categories,
                           now_dt=datetime.utcnow().strftime('%Y-%m-%dT%H:%M'), ai_enabled=is_enabled())


@admin_bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def blog_post_edit(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        flash(t('flash.post_not_found'), 'error')
        return redirect(url_for('admin.blog_posts_list'))

    categories = BlogCategory.query.order_by(BlogCategory.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash(t('flash.title_required'), 'error')
            return render_template('admin/blog/post_form.html', post=post, categories=categories, ai_enabled=is_enabled())

        has_es      = request.form.get('has_es') == '1'
        published   = request.form.get('published') == '1'
        category_id = request.form.get('category_id') or None

        created_at_raw = request.form.get('created_at', '').strip()
        try:
            created_at = datetime.strptime(created_at_raw, '%Y-%m-%dT%H:%M') if created_at_raw else post.created_at
        except ValueError:
            created_at = post.created_at

        post.title          = title
        post.description    = request.form.get('description', '').strip() or None
        post.has_es         = has_es
        post.title_es       = request.form.get('title_es', '').strip() or None if has_es else None
        post.description_es = request.form.get('description_es', '').strip() or None if has_es else None
        post.category_id    = int(category_id) if category_id else None
        post.published      = published
        post.created_at     = created_at
        post.tags           = _parse_tags(request.form.get('tags', ''))

        # Cover image
        cover = request.files.get('cover_image')
        if cover and cover.filename:
            ext = secure_filename(cover.filename).rsplit('.', 1)[-1].lower()
            cover_path = f'blog/posts/{post.slug}/cover.{ext}'
            if _store_img(cover, cover_path):
                if post.cover_image_path and post.cover_image_path != cover_path:
                    storage.delete(post.cover_image_path)
                post.cover_image_path = cover_path
            else:
                flash(t('flash.cover_rejected'), 'error')

        # Markdown EN
        md_en = request.files.get('markdown_file')
        if md_en and md_en.filename:
            path_en = f'blog/posts/{post.slug}/content_en.md'
            if _store_md(md_en, path_en):
                post.markdown_path = path_en
            else:
                flash(t('flash.en_md_rejected'), 'error')

        # Markdown ES
        if has_es:
            md_es = request.files.get('markdown_file_es')
            if md_es and md_es.filename:
                path_es = f'blog/posts/{post.slug}/content_es.md'
                if _store_md(md_es, path_es):
                    post.markdown_path_es = path_es
                else:
                    flash(t('flash.es_md_rejected'), 'error')

        db.session.commit()
        flash(t('flash.post_updated'), 'success')
        return redirect(url_for('admin.blog_post_edit', post_id=post.id))

    return render_template('admin/blog/post_form.html', post=post, categories=categories,
                           now_dt=datetime.utcnow().strftime('%Y-%m-%dT%H:%M'), ai_enabled=is_enabled())


@admin_bp.post('/blog/<int:post_id>/delete')
@login_required
def blog_post_delete(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        flash(t('flash.post_not_found'), 'error')
        return redirect(url_for('admin.blog_posts_list'))

    if post.cover_image_path:
        storage.delete(post.cover_image_path)
    if post.markdown_path:
        storage.delete(post.markdown_path)
    if post.markdown_path_es:
        storage.delete(post.markdown_path_es)
    for img in post.images:
        storage.delete(img.image_path)

    title = post.title
    db.session.delete(post)
    db.session.commit()
    flash(t('flash.post_deleted', title=title), 'success')
    return redirect(url_for('admin.blog_posts_list'))


@admin_bp.post('/blog/bulk-delete')
@login_required
def blog_posts_bulk_delete():
    ids = request.form.getlist('post_ids', type=int)
    if ids:
        posts = BlogPost.query.filter(BlogPost.id.in_(ids)).all()
        for post in posts:
            if post.cover_image_path:
                storage.delete(post.cover_image_path)
            if post.markdown_path:
                storage.delete(post.markdown_path)
            if post.markdown_path_es:
                storage.delete(post.markdown_path_es)
            for img in post.images:
                storage.delete(img.image_path)
        deleted = (
            BlogPost.query
            .filter(BlogPost.id.in_(ids))
            .delete(synchronize_session=False)
        )
        db.session.commit()
        flash(t('flash.posts_bulk_deleted', n=deleted), 'success')
    else:
        flash(t('flash.no_posts_selected'), 'error')
    return redirect(url_for('admin.blog_posts_list'))


# ── Publish toggle (AJAX) ─────────────────────────────────────────────────────

@admin_bp.post('/blog/<int:post_id>/toggle-publish')
@login_required
def blog_post_toggle_publish(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        return jsonify({'error': 'Post not found.'}), 404
    post.published = not post.published
    db.session.commit()
    return jsonify({'published': post.published})


# ── AI suggestions (AJAX) ─────────────────────────────────────────────────────

@admin_bp.post('/blog/ai/suggest-metadata')
@login_required
def blog_ai_suggest_metadata():
    if not is_enabled():
        return jsonify({'error': t('flash.ai_not_configured')}), 503

    title = request.form.get('title', '').strip()
    if not title:
        return jsonify({'error': t('flash.ai_title_required')}), 400

    language = request.form.get('language', 'en').strip().lower()
    if language not in ('en', 'es'):
        language = 'en'
    include_tags = language == 'en'  # tags are shared across languages — only generate them once, from EN

    markdown_content = ''
    md_file = request.files.get('markdown_file')
    if md_file and md_file.filename:
        if not _allowed_md(md_file.filename):
            return jsonify({'error': t('flash.en_md_rejected')}), 400
        content = md_file.read()
        if len(content) > MAX_MD_BYTES:
            return jsonify({'error': t('flash.en_md_rejected')}), 400
        markdown_content = content.decode('utf-8', errors='ignore')
    else:
        post_id = request.form.get('post_id', type=int)
        if post_id:
            post = db.session.get(BlogPost, post_id)
            path = (post.markdown_path_es if language == 'es' else post.markdown_path) if post else None
            if path:
                markdown_content = storage.get(path).decode('utf-8', errors='ignore')

    existing_tags = [name for (name,) in db.session.query(BlogTag.name).all()] if include_tags else None

    try:
        suggestion = suggest_blog_metadata(
            title=title, markdown_content=markdown_content, language=language,
            existing_tags=existing_tags, include_tags=include_tags,
        )
    except AIServiceError as exc:
        return jsonify({'error': str(exc)}), 502

    return jsonify(suggestion)


# ── Post images (AJAX) ────────────────────────────────────────────────────────

@admin_bp.post('/blog/<int:post_id>/images')
@login_required
def blog_post_add_image(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        return jsonify({'error': 'Post not found.'}), 404

    file = request.files.get('image')
    if not file or not file.filename:
        return jsonify({'error': 'No image selected.'}), 400

    filename = secure_filename(file.filename)
    path = f'blog/posts/{post.slug}/images/{filename}'
    if _store_img(file, path):
        img = BlogPostImage(post_id=post_id, image_path=path)
        db.session.add(img)
        db.session.commit()
        return jsonify({
            'id':  img.id,
            'url': url_for('serve_media', file_path=path),
        })

    return jsonify({'error': 'Image rejected — invalid type or exceeds 5 MB.'}), 400


@admin_bp.post('/blog/<int:post_id>/images/<int:image_id>/delete')
@login_required
def blog_post_delete_image(post_id, image_id):
    img = db.session.get(BlogPostImage, image_id)
    if img and img.post_id == post_id:
        storage.delete(img.image_path)
        db.session.delete(img)
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify({'error': 'Image not found.'}), 404



