from . import kanarianlintu_bp, log_hit
from flask import Response, render_template

@kanarianlintu_bp.route('/.env')
def env():
    log_hit('.env')
    content = render_template('kanarianlintu/env.txt')
    return Response(content, mimetype='text/plain')