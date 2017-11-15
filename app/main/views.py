from flask import render_template, redirect, url_for, request, current_app
from functools import wraps

from .. import db
from . import main
from .forms import *
from ..models import *


@main.route('/')
@main.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items if post.draft == False]
    return render_template('index.html',
                           title='首页',
                           posts=posts,
                           pagination=pagination)

@main.route('/<int:year>/<int:month>/<article_name>/')
def post(year, month, article_name):
    pass

@main.route('/about/')
def about():
    pass

@main.route('/tag/<tag_name>/')
def tag(tag_name):
    pass

@main.route('/category/<category_name>/')
def category(category_name):
    pass

@main.route('/archives/')
def archives():
    pass

@main.route('/comments/')
def comment():
    pass

@main.route('/search/')
# url_for('main.search', {keywords: xxx})
def search():
    search = request.args.get('keywords')
    pass

