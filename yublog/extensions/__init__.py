from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_whooshee import Whooshee
from flask_caching import Cache
from flask_migrate import Migrate

from yublog.extensions.picbed.qiniu import QiniuUpload

migrate = Migrate()
db = SQLAlchemy()
whooshee = Whooshee()
cache = Cache()
qn = QiniuUpload()
lm = LoginManager()
lm.login_view = "admin.login"
