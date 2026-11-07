from . import kanarianlintu_bp, log_hit
from .decoys import resolve_decoy
from flask import abort, request

@kanarianlintu_bp.route('/fail', methods=['GET', 'POST'])
def fail():
    resource = request.args.get('path') or request.path
    log_hit(resource)
    response = resolve_decoy(resource)
    if response is not None:
        return response
    return abort(404, description="This is a custom 404 error message for the /fail route.")