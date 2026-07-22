from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/no-css')
def no_css():
    # Deliberately does NOT extend base/base.html — that layout hardcodes
    # styles.css, Google Fonts, and the Font Awesome CDN in its <head>,
    # which would make an honest "zero stylesheets" claim false.
    return render_localized_template('nerd/no_css.html')
