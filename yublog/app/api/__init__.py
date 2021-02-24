from flask import Blueprint

api = Blueprint('api', __name__)

from yublog.app.api import views