from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
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

	from app.routes.home import home_bp
	app.register_blueprint(home_bp)

	from app.routes.utils import utils_bp
	app.register_blueprint(utils_bp)

	@app.errorhandler(404)
	def not_found(error):
		return render_template('404.html'), 404

	return app
