from . import kanarianlintu_bp
from flask import render_template

@kanarianlintu_bp.route('/server')
def server():
    return render_template('kanarianlintu/server.html')