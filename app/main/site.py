from flask import send_from_directory

from . import main
from ..models import Post
from ..utils import get_sitemap, save_file


@main.route('/sitemap.xml')
def sitemap():
    post_list = Post.query.order_by(Post.timestamp.desc()).all()
    posts = [post for post in post_list if post.draft==False]
    sitemap = get_sitemap(posts)
    save_file(sitemap)
    return send_from_directory('static','sitemap.xml')

@main.route('/robots.txt')
def robots():
    return send_from_directory('static','robots.txt')

