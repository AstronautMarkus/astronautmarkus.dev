from . import kanarianlintu_bp
from flask import redirect, url_for

@kanarianlintu_bp.route('/.env')
def env():
    return redirect("https://www.youtube.com/watch?v=eIYSSaWHqSM", code=302)