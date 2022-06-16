from flask import render_template

from yublog.views import main_bp


@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("error/404.html", title="404"), 404


@main_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template("error/500.html", title="500"), 500

