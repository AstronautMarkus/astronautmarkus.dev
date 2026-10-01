from flask import render_template, url_for

from app.models.models import BlogCategory, BlogPost, PortfolioProject
from . import utils_bp

# Public pages linked from the main nav; blog posts, categories and
# portfolio projects are added from the database.
SITEMAP_PAGES = (
    'main.home',
    'main.about_me',
    'main.portfolio_list',
    'main.blog_list',
    'main.gallery_list',
    'main.homelab',
    'main.setup',
    'main.beercat',
    'main.guestbook',
    'contact.contact',
    'extras.pdf_generator',
)


@utils_bp.route('/robots.txt')
def robots():
    return render_template('robots.txt'), 200, {'Content-Type': 'text/plain'}


@utils_bp.route('/sitemap.xml')
def sitemap():
    urls = [{'loc': url_for(endpoint, _external=True)} for endpoint in SITEMAP_PAGES]

    posts = (
        BlogPost.query
        .filter_by(published=True)
        .order_by(BlogPost.created_at.desc())
        .all()
    )
    urls += [
        {
            'loc': url_for('main.blog_post_detail', slug=post.slug, _external=True),
            'lastmod': post.created_at.strftime('%Y-%m-%d'),
        }
        for post in posts
    ]

    categories = (
        BlogCategory.query
        .filter(BlogCategory.posts.any(BlogPost.published.is_(True)))
        .order_by(BlogCategory.name)
        .all()
    )
    urls += [{'loc': url_for('main.blog_category_detail', slug=cat.slug, _external=True)} for cat in categories]

    projects = PortfolioProject.query.order_by(PortfolioProject.created_at.desc()).all()
    urls += [
        {
            'loc': url_for('main.portfolio_detail', project_id=project.id, _external=True),
            'lastmod': project.created_at.strftime('%Y-%m-%d'),
        }
        for project in projects
    ]

    return render_template('sitemap.xml', urls=urls), 200, {'Content-Type': 'application/xml'}
