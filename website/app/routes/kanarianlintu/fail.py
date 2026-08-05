from . import kanarianlintu_bp
from flask import abort

@kanarianlintu_bp.route('/fail')
def fail():
    return abort(404, description="This is a custom 404 error message for the /fail route.")