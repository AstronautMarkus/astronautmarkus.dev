from datetime import datetime, timedelta

from flask import current_app, request

from app import db
from app.models.models import Visit


def _is_valid_request_for_visit_register() -> bool:
	if request.method != 'GET':
		return False

	if request.endpoint and request.endpoint == 'static':
		return False

	return True


def _extract_utm_source_and_presence() -> tuple[str | None, bool]:
	utm_params = {}

	for key, value in request.args.items():
		if key.startswith('utm_'):
			cleaned_value = (value or '').strip()
			if cleaned_value:
				utm_params[key] = cleaned_value

	legacy_utm_source = request.args.get('utm', type=str)
	if legacy_utm_source and legacy_utm_source.strip():
		utm_params.setdefault('utm_source', legacy_utm_source.strip())

	has_utm_params = bool(utm_params)
	utm_source = utm_params.get('utm_source')

	if not utm_source and has_utm_params:
		utm_source = '|'.join(f'{key}:{value}' for key, value in sorted(utm_params.items()))

	if utm_source:
		utm_source = utm_source[:100]

	return utm_source, has_utm_params


def register_visit_middleware() -> None:
	if not _is_valid_request_for_visit_register():
		return

	ip_address = request.remote_addr
	if not ip_address:
		return

	user_agent = request.headers.get('User-Agent')
	utm_source, has_utm_params = _extract_utm_source_and_presence()

	last_visit = (
		Visit.query
		.filter_by(ip_address=ip_address)
		.order_by(Visit.visited_at.desc())
		.first()
	)

	if last_visit and last_visit.visited_at:
		elapsed = current_app.config.get('VISIT_REGISTER_INTERVAL_HOURS', 24)
		cutoff = datetime.utcnow() - timedelta(hours=elapsed)
		if last_visit.visited_at > cutoff:
			return

	try:
		visit = Visit(ip_address=ip_address, user_agent=user_agent, utm_source=utm_source)
		db.session.add(visit)
		db.session.commit()
	except Exception:
		db.session.rollback()


def init_visit_middleware(app) -> None:
	app.before_request(register_visit_middleware)
