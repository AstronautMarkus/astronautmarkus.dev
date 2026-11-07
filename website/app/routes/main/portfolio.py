from flask import abort, redirect, request, url_for

from app import db
from app.i18n import get_current_language, render_localized_template
from app.models.models import PortfolioProject
from app.routes.main import main_bp
from app.storage import storage
from app.tech_stack import get_tags
from app.utils import expand_media_shorthand, render_markdown


@main_bp.get('/portfolio/')
def portfolio_list():
    lang = get_current_language()
    projects = (
        PortfolioProject.query
        .order_by(PortfolioProject.featured.desc(), PortfolioProject.created_at.desc())
        .all()
    )

    tags_by_project = {p.id: get_tags(p.tech_list, lang) for p in projects}
    counts = {}
    for tags in tags_by_project.values():
        for tag in tags:
            entry = counts.setdefault(tag['key'].lower(), {**tag, 'count': 0})
            entry['count'] += 1
    tech_filters = sorted(counts.values(), key=lambda tag: (-tag['count'], tag['name'].lower()))

    requested = request.args.get('tech', '').strip().lower()
    active_tech = requested if requested in counts else ''
    if active_tech:
        projects = [
            p for p in projects
            if any(tag['key'].lower() == active_tech for tag in tags_by_project[p.id])
        ]

    return render_localized_template(
        'main/portfolio_list.html',
        projects=projects,
        tags_by_project=tags_by_project,
        tech_filters=tech_filters,
        active_tech=active_tech,  # lowercase key; compare with tag.key|lower
    )


@main_bp.get('/portfolio/<slug>')
def portfolio_detail(slug):
    project = PortfolioProject.query.filter_by(slug=slug).first()
    if project is None:
        # Old /portfolio/<id> links (shared, indexed) move permanently to the slug URL.
        project = db.session.get(PortfolioProject, int(slug)) if slug.isdecimal() else None
        if project is None:
            abort(404)
        return redirect(url_for('main.portfolio_detail', slug=project.slug), 301)

    lang = get_current_language()
    use_es = lang == 'es' and project.has_es
    md_path = (project.markdown_path_es or project.markdown_path) if use_es else project.markdown_path

    content_html = None
    if md_path and storage.exists(md_path):
        raw = storage.get(md_path)
        if raw:
            text = expand_media_shorthand(raw.decode('utf-8'), f'portfolio/extras/{project.id}')
            content_html = render_markdown(text)

    return render_localized_template(
        'main/portfolio_detail.html',
        project=project,
        content_html=content_html,
        tags=get_tags(project.tech_list, lang),
    )
