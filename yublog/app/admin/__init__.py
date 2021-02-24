from flask import Blueprint

admin = Blueprint('admin', __name__)

from yublog.app.admin import views