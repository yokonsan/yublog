import os
import asyncio

import click
from flask import Flask, g

from yublog.extensions import migrate, db, whooshee, cache, qn, lm
from yublog.caches import cache_tool, global_cache_key
from yublog.forms import SearchForm, MobileSearchForm
from yublog.config import config
from yublog.models import Admin, SiteLink, Tag, \
    Page, Post, Category, LoveMe, Talk, SideBox, Comment
from yublog.views import main_bp, admin_bp, api_bp, column_bp


@lm.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


def create_app(config_name=None):
    config_name = config_name or os.getenv('CONFIG', 'default')
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)

    return app


def register_blueprints(app):

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(column_bp, url_prefix='/column')


def register_extensions(app):
    db.init_app(app)
    lm.init_app(app)
    whooshee.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)

    if app.config.get('NEED_PIC_BED', False):
        qn.init_app(app)


def register_shell_context_processor(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(app=app, db=db, Admin=Admin, Post=Post, Tag=Tag,
                    Category=Category, SiteLink=SiteLink, Page=Page,
                    LoveMe=LoveMe, Comment=Comment, Talk=Talk, SideBox=SideBox)


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', default=True, help='Create after drop.')
    def init_db(drop):
        if drop:
            db.drop_all()
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command()
    @click.option('--username', prompt=True,
                  default=app.config.get('ADMIN_LOGIN_NAME', ''),
                  help='The username used to login.')
    @click.option('--password', prompt=True,
                  default=app.config.get('ADMIN_PASSWORD', ''),
                  hide_input=True, help='The password used to login.')
    def deploy(username, password):
        # 创建管理员
        site_name = app.config.get('SITE_NAME', '')
        site_title = app.config.get('SITE_TITLE', '')
        name = app.config.get('ADMIN_NAME', '')
        profile = app.config.get('ADMIN_PROFILE', '')
        # login_name = app.config.get('ADMIN_LOGIN_NAME', '')
        # password = app.config.get('ADMIN_PASSWORD', '')
        admin = Admin(site_name=site_name, site_title=site_title, name=name,
                      profile=profile, login_name=username, password=password)
        # 创建部门数据模型
        love_data = LoveMe(love_me_count=0)
        # 创建留言板、关于
        guest_book_page = Page(title='留言板', url_name='guest-book', able_comment=True,
                               show_nav=False, body='留言板')
        about_page = Page(title='关于', url_name='about', able_comment=False,
                          show_nav=True, body='介绍下自己吧')
        talk = Talk(talk='hello world!')
        db.session.add(admin)
        db.session.add(love_data)
        db.session.add(guest_book_page)
        db.session.add(about_page)
        db.session.add(talk)
        db.session.commit()

    @app.cli.command()
    @click.option('--clear_alembic', default=True, help='Create after drop.')
    def clear_alembic():
        from yublog.models import Alembic
        Alembic.clear()


async def _global_data():
    """
    所有页面共有的，比如侧栏的标签集合，社交链接，博主信息，
    和导航栏的所有分类。
    :return: global_data = {
        'admin': admin, // model object
        'social_links': socaial_links, // object list
        'friend_links': friend_links, // ...
        'tags': tags, // ...
        'categories': categories, // ...
        'pages': pages, // ...
    }
    """
    global_data = {}
    administrator = Admin.query.first()
    links = SiteLink.query.order_by(SiteLink.id.desc()).all()
    categories = Category.query.filter_by(is_show=True).all()
    tags = Tag.query.all()
    pages = Page.query.filter_by(show_nav=True).all()
    love_me_counts = LoveMe.query.first()
    posts = Post.query.filter_by(draft=False).count()
    talk = Talk.query.order_by(Talk.timestamp.desc()).first()
    guest_book = Page.query.filter_by(url_name='guest-book').first()
    boxes = SideBox.query.order_by(SideBox.id.desc()).all()

    global_data[global_cache_key.ADMIN] = administrator
    global_data[global_cache_key.TAGS] = tags
    global_data[global_cache_key.CATEGORIES] = categories
    global_data[global_cache_key.PAGES] = pages
    global_data[global_cache_key.LOVE_COUNT] = love_me_counts.love_count
    global_data[global_cache_key.POST_COUNT] = posts
    global_data[global_cache_key.TALK] = talk.body_to_html
    guest_book_counts = guest_book.comments.count() if guest_book and guest_book.comments else 0
    global_data[global_cache_key.GUEST_BOOK_COUNT] = guest_book_counts

    if links:
        social_links = [link for link in links if link.is_friend is False]
        friend_links_counts = len(links) - len(social_links)
        global_data[global_cache_key.SOCIAL_LINKS] = social_links
        global_data[global_cache_key.FRIEND_COUNT] = friend_links_counts
    if boxes:
        adv_boxes = [box for box in boxes if box.unable is False and box.is_advertising is True]
        global_data[global_cache_key.ADS_BOXES] = adv_boxes
        my_boxes = [box for box in boxes if box.unable is False and box.is_advertising is False]
        global_data[global_cache_key.MY_BOXES] = my_boxes

    cache_tool.set(cache_tool.GLOBAL_KEY, global_data, timeout=60*60*24*30)
    return global_data


@main_bp.app_context_processor
def app_global_data():
    return asyncio.run(_global_data())


@main_bp.before_request
def before_request():
    g.search_form = SearchForm()
    g.search_form2 = MobileSearchForm()


"""
add_app_template_global is the problem of legacy slowing down the program.
add_app_template_global is register a custom template global application.
app_context_processor decorator is register a custom template global dict.
"""

