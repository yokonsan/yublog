from flask import Blueprint


main_bp = Blueprint("main", __name__)
column_bp = Blueprint("column", __name__)
api_bp = Blueprint("api", __name__)
admin_bp = Blueprint("admin", __name__)
image_bp = Blueprint("image", __name__)


from yublog.views import main, admin, column, site, api, error, image  # noqa
