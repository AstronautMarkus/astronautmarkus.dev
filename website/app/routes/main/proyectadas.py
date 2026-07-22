from app.i18n import render_localized_template
from app.models.models import Proyectada
from app.routes.main import main_bp


@main_bp.get('/proyectadas/')
def proyectadas_list():
    items = (
        Proyectada.query
        .filter_by(published=True)
        .order_by(Proyectada.created_at.desc())
        .all()
    )
    return render_localized_template('main/proyectadas.html', items=items)
