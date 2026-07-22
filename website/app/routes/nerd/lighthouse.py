from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp

# Self-reported, entirely made up. Nobody ran Chrome DevTools for this.
SCORES = {
    'performance': 99,
    'accessibility': 97,
    'best_practices': 100,
    'seo': 100,
}


@nerd_bp.route('/lighthouse')
def lighthouse():
    return render_localized_template('nerd/lighthouse.html', scores=SCORES)
