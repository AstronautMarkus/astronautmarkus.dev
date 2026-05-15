from flask import Flask, render_template, request, redirect, url_for, g
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
