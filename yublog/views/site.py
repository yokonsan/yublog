from flask import send_from_directory

from yublog.views import main_bp


@main_bp.route("/sitemap.xml")
def sitemap():
    return send_from_directory("static", "sitemap.xml")


@main_bp.route("/robots.txt")
def robots():
    return send_from_directory("static", "robots.txt")


@main_bp.route("/atom.xml")
def rss():
    return send_from_directory("static", "atom.xml")


@main_bp.route("/<filename>/")
def get_file(filename):
    return send_from_directory("static", f"upload/{filename}")


@main_bp.route("/<path>/<filename>/")
def get_dir_file(path, filename):
    return send_from_directory("static", f"upload/{path}/{filename}")


@main_bp.route("/init")
def init():
    pass
