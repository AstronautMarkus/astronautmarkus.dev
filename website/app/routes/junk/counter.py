from app.i18n import render_localized_template
from app.models.models import Visit
from app.routes.junk import junk_bp
from app.routes.junk._ring import ring_nav


@junk_bp.route('/counter')
def counter():
    total_visits = Visit.query.count()
    return render_localized_template(
        'junk/counter.html',
        total_visits=total_visits,
        **ring_nav('junk.counter'),
    )
