from flask import url_for

from app.i18n import render_localized_template
from app.routes.junk import junk_bp
from app.routes.junk._ring import ring_nav


@junk_bp.route('/links')
def links():
    button_url = url_for('static', filename='images/88-31/button.png', _external=True)
    home_url = url_for('main.home', _external=True)
    return render_localized_template(
        'junk/links.html',
        button_url=button_url,
        home_url=home_url,
        **ring_nav('junk.links'),
    )
