from app.i18n import render_localized_template
from app.routes.nerd import nerd_bp


@nerd_bp.route('/size')
def size():
    # Render once to measure, then again with the real number filled in —
    # the second pass differs by only the few bytes needed for the digits.
    html = render_localized_template('nerd/size.html', page_bytes=0, page_kb=0)
    page_bytes = len(html.encode('utf-8'))
    page_kb = round(page_bytes / 1024, 1)
    return render_localized_template('nerd/size.html', page_bytes=page_bytes, page_kb=page_kb)
