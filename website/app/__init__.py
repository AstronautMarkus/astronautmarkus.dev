from flask import Flask, render_template, request, redirect, url_for, g, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from datetime import datetime
from app.config.config import Config
from app.i18n import (
    SUPPORTED_LANGUAGES,
    LANG_COOKIE_NAME,
    DEFAULT_LANGUAGE,
    get_current_language,
    render_localized_template,
)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.routing import RequestRedirect as _WerkzeugRedirect
from werkzeug.exceptions import NotFound as _WerkzeugNotFound

db      = SQLAlchemy()
migrate = Migrate()
mail    = Mail()

def create_app():
	app = Flask(__name__)
	app.config.from_object(Config)

	db.init_app(app)
	migrate.init_app(app, db)
	mail.init_app(app)

	app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
	from app.middleware.register_visit import init_visit_middleware
	init_visit_middleware(app)

	# ── /es/<path> and /en/<path> prefix redirect ───────────────
	@app.before_request
	def redirect_lang_prefix():
		path = request.path

		for lang in SUPPORTED_LANGUAGES:
			# exact /es or /en  →  redirect to /
			if path in (f'/{lang}', f'/{lang}/'):
				response = redirect('/')
				response.set_cookie(LANG_COOKIE_NAME, lang, max_age=60 * 60 * 24 * 365, samesite='Lax')
				return response

			# /es/<subpath> or /en/<subpath>
			prefix = f'/{lang}/'
			if path.startswith(prefix):
				clean_path = path[len(f'/{lang}'):]

				try:
					app.url_map.bind('').match(clean_path, method=request.method)
				except _WerkzeugNotFound:
					abort(404)
				except _WerkzeugRedirect:
					pass

				qs = request.query_string.decode()
				target = f'{clean_path}?{qs}' if qs else clean_path
				response = redirect(target)
				response.set_cookie(LANG_COOKIE_NAME, lang, max_age=60 * 60 * 24 * 365, samesite='Lax')
				return response

	# ── Language detection ────────────────────────────────────────
	@app.before_request
	def detect_language():
		lang = request.cookies.get(LANG_COOKIE_NAME)
		if lang not in SUPPORTED_LANGUAGES:
			lang = request.accept_languages.best_match(SUPPORTED_LANGUAGES) or DEFAULT_LANGUAGE
		g.current_lang = lang

	# ── Language switcher route ───────────────────────────────────
	@app.get('/lang/<lang_code>')
	def set_language(lang_code):
		lang = lang_code.lower()
		if lang not in SUPPORTED_LANGUAGES:
			lang = DEFAULT_LANGUAGE

		next_url = request.args.get('next', '/')
		if not next_url.startswith('/'):
			next_url = '/'

		response = redirect(next_url)
		response.set_cookie(
			LANG_COOKIE_NAME,
			lang,
			max_age=60 * 60 * 24 * 365,
			samesite='Lax',
		)
		return response

	# ── Blueprints ────────────────────────────────────────────────
	from app.routes.main import main_bp
	app.register_blueprint(main_bp)

	# ── Template globals ──────────────────────────────────────────
	@app.context_processor
	def inject_globals():
		return {
			'current_year': datetime.now().year,
			'current_lang': get_current_language(),
		}

	return app
