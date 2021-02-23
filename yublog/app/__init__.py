from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_whooshee import Whooshee
from flask_caching import Cache

from yublog.config import config
from yublog.app.utils.qiniu_picbed import QiniuUpload
db = SQLAlchemy()
lm = LoginManager()
lm.login_view = 'admin.login'

whooshee = Whooshee()
cache = Cache()
qn = QiniuUpload()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    lm.init_app(app)
    whooshee.init_app(app)
    cache.init_app(app)

    if app.config.get('NEED_PIC_BED', False):
        qn.init_app(app)

    from yublog.app.main import main as main_blueprint
    from yublog.app.admin import admin as admin_blueprint
    from yublog.app.api import api as api_blueprint
    from yublog.app.main import column as column_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.register_blueprint(column_blueprint, url_prefix='/column')

    return app
