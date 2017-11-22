from flask import render_template, redirect, url_for, request, current_app

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
    timestamps = [post.timestamp for post in posts]
    data = {}
    for post, time in zip(posts, timestamps):
        data = {post: moment_timestamp(time)}
    return render_template('index.html',
                           title='首页',
                           data=data,
                           pagination=pagination)

def moment_timestamp(timestamp):
    """
    存入数据库的post日期是Integer，
    需要以'-'分割成正式日期返回
    """
    timestamp = str(timestamp)
    return timestamp[0:3] + '-' + timestamp[4:5] + '-' + timestamp[6:7]

@main.route('/<int:time>/<article_name>/')
def post(time, article_name):
    post = Post.query.filter_by(timestamp=time, url_name=article_name).first()
    if post:
        post.view_num += 1
        db.session.add(post)
        time = moment_timestamp(post.timestamp)

        return render_template('post.html', post=post, time=time)
    return None

@main.route('/<page_name>/')
def page(page_name):
    page = Page.query.filter_by(page=page_name).first()

    return render_template('page.html', page=page)

@main.route('/tag/<tag_name>/')
def tag(tag_name):
    tag = Tag.query.filter_by(tag=tag_name).first()
    all_posts = Post.order_by().all()
    posts = [post for post in all_posts if post.tag_in_post(tag.tag)]
    return render_template('tag.html', tag=tag, posts=posts)

@main.route('/category/<category_name>/')
def category(category_name):
    category = Category.query.filter_by(category=category_name).first()
    posts = Post.query.filter(category=category.category).all()
    return render_template('category.html', category=category, posts=posts)

@main.route('/archives/')
def archives():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = [post for post in pagination.items if post.draft == False]
    return render_template('archives.html',
                           title='归档',
                           posts=posts,
                           pagination=pagination)

@main.route('/search/')
# url_for('main.search', {keywords: xxx})
def search():
    search = request.args.get('keywords')
    pass

