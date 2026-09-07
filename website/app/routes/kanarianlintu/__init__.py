from flask import Blueprint, request

kanarianlintu_bp = Blueprint('kanarianlintu', __name__)


def log_hit(resource=None):
    """Persist a HoneypotHit with every legally-observable detail of the request (IP, UA, headers, target, body)."""
    from app import db
    from app.models.models import HoneypotHit

    body = None
    if request.method in ('POST', 'PUT', 'PATCH'):
        raw = request.get_data()
        body = raw.decode('utf-8', errors='replace')[:4000] if raw else None

    hit = HoneypotHit(
        ip_address=request.remote_addr or '0.0.0.0',
        x_forwarded_for=request.headers.get('X-Forwarded-For'),
        user_agent=request.headers.get('User-Agent'),
        method=request.method,
        endpoint=request.endpoint,
        path=request.path,
        query_string=request.query_string.decode('utf-8', 'ignore') or None,
        resource=resource,
        referrer=request.headers.get('Referer'),
        accept_language=request.headers.get('Accept-Language'),
        headers='\n'.join(f'{k}: {v}' for k, v in request.headers.items()),
        body=body,
    )

    try:
        db.session.add(hit)
        db.session.commit()
    except Exception:
        db.session.rollback()


from . import server, env, fail, decoys  # noqa: E402, F401