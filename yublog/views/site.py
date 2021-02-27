from flask import send_from_directory

from yublog.views import main_bp


@main_bp.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')


@main_bp.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')


@main_bp.route('/atom.xml')
def rss():
    return send_from_directory('static', 'atom.xml')


@main_bp.route('/<filename>/')
def get_file(filename):
    # print(filename)
    return send_from_directory('static', 'upload/{0}'.format(filename))


@main_bp.route('/<path>/<filename>/')
def get_dir_file(path, filename):
    # print(f'{path}/{filename}')
    return send_from_directory('static', 'upload/{path}/{filename}'.format(path=path, filename=filename))
