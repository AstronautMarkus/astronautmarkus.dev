from flask import abort

from app import db
from app.i18n import get_current_language, render_localized_template
from app.models.models import PortfolioProject
from app.routes.main import main_bp
from app.storage import storage
from app.utils import expand_media_shorthand, render_markdown


@main_bp.get('/portfolio/')
def portfolio_list():
    projects = (
        PortfolioProject.query
        .order_by(PortfolioProject.created_at.desc())
        .all()
    )
    return render_localized_template('main/portfolio_list.html', projects=projects)


@main_bp.get('/portfolio/<int:project_id>')
def portfolio_detail(project_id):
    project = db.session.get(PortfolioProject, project_id)
    if project is None:
        abort(404)

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
    )
