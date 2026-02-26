from flask import render_template
from . import home_bp

@home_bp.route('/external-links')
def external_links():
    return render_template('external_links.html')

@home_bp.route('/es/external-links')
def external_links_es():
    return render_template('/es/external_links.html')