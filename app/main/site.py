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
