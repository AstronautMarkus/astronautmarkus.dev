import re

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from app import db
from app.models.models import BlogCategory, BlogPost, BlogPostImage
from app.routes.admin import admin_bp
from app.storage import storage

ALLOWED_MD  = {'md', 'markdown'}
ALLOWED_IMG = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
MAX_MD_BYTES  = 2 * 1024 * 1024   # 2 MB
MAX_IMG_BYTES = 5 * 1024 * 1024   # 5 MB


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


def _unique_slug(base: str, exclude_id: int | None = None) -> str:
    slug = base
    i = 2
    while True:
        q = BlogPost.query.filter_by(slug=slug)
        if exclude_id:
            q = q.filter(BlogPost.id != exclude_id)
        if not q.first():
            return slug
        slug = f'{base}-{i}'
        i += 1


# ══ Categories ════════════════════════════════════════════════════════════════

@admin_bp.get('/blog/categories/')
@login_required
def blog_categories_list():
    categories = BlogCategory.query.order_by(BlogCategory.name).all()
    return render_template('admin/blog/category_list.html', categories=categories)


@admin_bp.route('/blog/categories/create', methods=['GET', 'POST'])
@login_required
def blog_category_create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Category name is required.', 'error')
            return render_template('admin/blog/category_form.html', category=None)

        has_es = request.form.get('has_es') == '1'
        name_es = request.form.get('name_es', '').strip() or None

        cat = BlogCategory(
            name=name,
            has_es=has_es,
            name_es=name_es if has_es else None,
        )
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" created.', 'success')
        return redirect(url_for('admin.blog_categories_list'))

    return render_template('admin/blog/category_form.html', category=None)


@admin_bp.route('/blog/categories/<int:cat_id>/edit', methods=['GET', 'POST'])
@login_required
def blog_category_edit(cat_id):
    category = db.session.get(BlogCategory, cat_id)
    if category is None:
        flash('Category not found.', 'error')
        return redirect(url_for('admin.blog_categories_list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Category name is required.', 'error')
            return render_template('admin/blog/category_form.html', category=category)

        has_es = request.form.get('has_es') == '1'
        name_es = request.form.get('name_es', '').strip() or None

        category.name = name
        category.has_es = has_es
        category.name_es = name_es if has_es else None
        db.session.commit()
        flash('Category updated.', 'success')
        return redirect(url_for('admin.blog_category_edit', cat_id=category.id))

    return render_template('admin/blog/category_form.html', category=category)


@admin_bp.post('/blog/categories/<int:cat_id>/delete')
@login_required
def blog_category_delete(cat_id):
    category = db.session.get(BlogCategory, cat_id)
    if category is None:
        flash('Category not found.', 'error')
        return redirect(url_for('admin.blog_categories_list'))

    if category.posts:
        flash(
            f'Cannot delete "{category.name}" — {len(category.posts)} post(s) are assigned to it.',
            'error',
        )
        return redirect(url_for('admin.blog_categories_list'))

    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f'Category "{name}" deleted.', 'success')
    return redirect(url_for('admin.blog_categories_list'))


# ══ Posts ══════════════════════════════════════════════════════════════════════

@admin_bp.get('/blog/')
@login_required
def blog_posts_list():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog/post_list.html', posts=posts)


@admin_bp.route('/blog/create', methods=['GET', 'POST'])
@login_required
def blog_post_create():
    categories = BlogCategory.query.order_by(BlogCategory.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return render_template('admin/blog/post_form.html', post=None, categories=categories)

        has_es      = request.form.get('has_es') == '1'
        published   = request.form.get('published') == '1'
        category_id = request.form.get('category_id') or None
        slug_input  = request.form.get('slug', '').strip()
        base_slug   = _slugify(slug_input) if slug_input else _slugify(title)

        post = BlogPost(
            title=title,
            description=request.form.get('description', '').strip() or None,
            has_es=has_es,
            title_es=request.form.get('title_es', '').strip() or None if has_es else None,
            description_es=request.form.get('description_es', '').strip() or None if has_es else None,
            category_id=int(category_id) if category_id else None,
            published=published,
            slug='__tmp__',
        )
        db.session.add(post)
        db.session.flush()

        post.slug = _unique_slug(base_slug, exclude_id=post.id)

        # Cover image
        cover = request.files.get('cover_image')
        if cover and cover.filename:
            ext = secure_filename(cover.filename).rsplit('.', 1)[-1].lower()
            cover_path = f'blog/posts/{post.slug}/cover.{ext}'
            if _store_img(cover, cover_path):
                post.cover_image_path = cover_path
            else:
                flash('Cover image rejected — invalid type or exceeds 5 MB.', 'error')

        # Markdown EN
        md_en = request.files.get('markdown_file')
        if md_en and md_en.filename:
            path_en = f'blog/posts/{post.slug}/content_en.md'
            if _store_md(md_en, path_en):
                post.markdown_path = path_en
            else:
                flash('EN Markdown rejected — must be a .md file under 2 MB.', 'error')

        # Markdown ES
        if has_es:
            md_es = request.files.get('markdown_file_es')
            if md_es and md_es.filename:
                path_es = f'blog/posts/{post.slug}/content_es.md'
                if _store_md(md_es, path_es):
                    post.markdown_path_es = path_es
                else:
                    flash('ES Markdown rejected — must be a .md file under 2 MB.', 'error')

        db.session.commit()
        flash(f'Post "{post.title}" created.', 'success')
        return redirect(url_for('admin.blog_post_edit', post_id=post.id))

    return render_template('admin/blog/post_form.html', post=None, categories=categories)


@admin_bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def blog_post_edit(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        flash('Post not found.', 'error')
        return redirect(url_for('admin.blog_posts_list'))

    categories = BlogCategory.query.order_by(BlogCategory.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title is required.', 'error')
            return render_template('admin/blog/post_form.html', post=post, categories=categories)

        has_es      = request.form.get('has_es') == '1'
        published   = request.form.get('published') == '1'
        category_id = request.form.get('category_id') or None

        post.title          = title
        post.description    = request.form.get('description', '').strip() or None
        post.has_es         = has_es
        post.title_es       = request.form.get('title_es', '').strip() or None if has_es else None
        post.description_es = request.form.get('description_es', '').strip() or None if has_es else None
        post.category_id    = int(category_id) if category_id else None
        post.published      = published

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
                flash('Cover image rejected — invalid type or exceeds 5 MB.', 'error')

        # Markdown EN
        md_en = request.files.get('markdown_file')
        if md_en and md_en.filename:
            path_en = f'blog/posts/{post.slug}/content_en.md'
            if _store_md(md_en, path_en):
                post.markdown_path = path_en
            else:
                flash('EN Markdown rejected — must be a .md file under 2 MB.', 'error')

        # Markdown ES
        if has_es:
            md_es = request.files.get('markdown_file_es')
            if md_es and md_es.filename:
                path_es = f'blog/posts/{post.slug}/content_es.md'
                if _store_md(md_es, path_es):
                    post.markdown_path_es = path_es
                else:
                    flash('ES Markdown rejected — must be a .md file under 2 MB.', 'error')

        db.session.commit()
        flash('Post updated.', 'success')
        return redirect(url_for('admin.blog_post_edit', post_id=post.id))

    return render_template('admin/blog/post_form.html', post=post, categories=categories)


@admin_bp.post('/blog/<int:post_id>/delete')
@login_required
def blog_post_delete(post_id):
    post = db.session.get(BlogPost, post_id)
    if post is None:
        flash('Post not found.', 'error')
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
    flash(f'Post "{title}" deleted.', 'success')
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



