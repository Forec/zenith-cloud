from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown
from config import config
import os, pymysql
pymysql.install_as_MySQLdb()

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
pagedown = PageDown()

login_manager.session_protection = 'strong' # None/basic/strong
login_manager.login_view = 'auth.login'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix = '/auth')

    try:
        os.mkdir(config[config_name].ZENITH_FILE_STORE_PATH)
    except:
        pass
    try:
        os.mkdir(config[config_name].ZENITH_TEMPFILE_STORE_PATH)
    except:
        pass

    return app