from flask import send_from_directory

from . import main


@main.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@main.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@main.route('/atom.xml')
def rss():
    return send_from_directory('static', 'atom.xml')

@main.route('/<filename>/')
def get_file(filename):
    print(filename)
    return send_from_directory('static', 'upload/{0}'.format(filename))

@main.route('/<path>/<filename>/')
def get_dir_file(path, filename):
    print('{path}/{filename}'.format(path=path, filename=filename))
    return send_from_directory('static', 'upload/{path}/{filename}'.format(path=path, filename=filename))
