from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from datetime import datetime
from app.config.config import Config
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app():
	app = Flask(__name__)
	app.config.from_object(Config)

	db.init_app(app)
	migrate.init_app(app, db)
	mail.init_app(app)

	app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
	from app.middleware.register_visit import init_visit_middleware
	init_visit_middleware(app)

	from app.routes.home import home_bp
	app.register_blueprint(home_bp)

	from app.routes.philosophy import philosophy_bp
	app.register_blueprint(philosophy_bp)

	from app.routes.utils import utils_bp
	app.register_blueprint(utils_bp)

	@app.errorhandler(404)
	def not_found(error):
		return render_template('/errors/404.html'), 404

	@app.context_processor
	def inject_current_year():
		return {'current_year': datetime.now().year}

	return app
