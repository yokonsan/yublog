from flask import Flask
from flask_sqlalchemy import SQLAlchemy, SignallingSession
from flask_login import LoginManager
from flask_whooshee import Whooshee
from flask_pagedown import PageDown

from config import config

# class MySQLAlchemy(SQLAlchemy):
#     def create_session(self, options):
#         options['autoflush'] = False
#         return SignallingSession(self, **options)

db = SQLAlchemy()
lm = LoginManager()
lm.login_view = 'admin.login'

whooshee = Whooshee()
pagedown = PageDown()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    lm.init_app(app)
    whooshee.init_app(app)
    pagedown.init_app(app)

    from .main import main as main_blueprint
    from .admin import admin as admin_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    return app
