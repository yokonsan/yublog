import os

import click
from flask import Flask, g, abort

from yublog.exceptions import AppInitException
from yublog.extensions import migrate, db, whooshee, cache, qn, lm
from yublog.utils.cache import cache_operate, CacheKey, CacheType
from yublog.forms import SearchForm, MobileSearchForm
from yublog.config import config
from yublog.models import (
    Admin,
    Link,
    Tag,
    Page,
    Post,
    Category,
    LoveMe,
    Talk,
    SideBox,
    Comment,
    ImagePath,
    Image,
)
from yublog.utils.log import log_time
from yublog.utils.times import nowstr
from yublog.views import main_bp, admin_bp, api_bp, column_bp, image_bp


@lm.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


def create_app(config_name=None):
    config_name = config_name or os.getenv("CONFIG", "default")
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)

    cache_operate.clean()

    return app


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(column_bp, url_prefix="/column")
    app.register_blueprint(image_bp, url_prefix="/image")


def register_extensions(app):
    db.init_app(app)
    lm.init_app(app)
    whooshee.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)

    if app.config.get("NEED_PIC_BED", False):
        qn.init_app(app)


def register_shell_context_processor(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(
            app=app,
            db=db,
            Admin=Admin,
            Post=Post,
            Tag=Tag,
            Category=Category,
            SiteLink=Link,
            Page=Page,
            LoveMe=LoveMe,
            Comment=Comment,
            Talk=Talk,
            SideBox=SideBox
        )


def register_commands(app):
    @app.cli.command()
    @click.option("--drop", prompt=False, default=False, help="Create after drop.", type=bool)
    def init_db(drop):
        """
        exception: sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) 
        (1045, "Access denied for user "root"@"localhost" (using password: NO)")

        Solution: 登入mysql，执行：ALTER USER "root"@"localhost" IDENTIFIED WITH mysql_native_password BY "数据库密码";
        """
        if drop:
            db.drop_all()
        db.create_all()
        click.echo("Initialized database.")

    @app.cli.command()
    @click.option("--username", prompt=False,
                  default=app.config.get("ADMIN_LOGIN_NAME", ""),
                  help="The username used to login.")
    @click.option("--password", prompt=False,
                  default=app.config.get("ADMIN_PASSWORD", ""),
                  hide_input=True, help="The password used to login.")
    def deploy(username, password):
        # 创建管理员
        name = app.config.get("ADMIN_NAME", "")
        if not Admin.query.first():
            admin = Admin(
                site_name=app.config.get("SITE_NAME", ""),
                site_title=app.config.get("SITE_TITLE", ""),
                username=name,
                profile=app.config.get("ADMIN_PROFILE", ""),
                login_name=username,
                password=password
            )
            db.session.add(admin)

        # 创建部门数据模型
        if not LoveMe.query.first():
            love_data = LoveMe(count=1)
            db.session.add(love_data)
        # 创建留言板、关于
        if not Page.query.first():
            guest_book_page = Page(
                title="GuestBook",
                url_name="guest-book",
                enable_comment=True,
                show_nav=False,
                body="Guest Book"
            )
            db.session.add(guest_book_page)
        if not Page.query.first():
            about_page = Page(
                title="关于",
                url_name="about",
                enable_comment=False,
                show_nav=True,
                body="Introduce yourself"
            )
            db.session.add(about_page)
        # 说说
        if not Talk.query.first():
            talk = Talk(talk="hello world!")
            db.session.add(talk)
        # 专栏链接
        if not Page.query.first():
            social_link = Link(link="/column/", name="专栏", is_friend=False)
            db.session.add(social_link)

        # hello world 文章
        if not Page.query.first():
            path = ImagePath(path="post0")
            for name in os.listdir(
                    os.path.join(app.config["IMAGE_UPLOAD_PATH"], "post0")
            ):
                db.session.add(Image(path="post0", filename=name, image_path=path))

        if not Post.query.first():
            with open(os.path.join(app.config["UPLOAD_PATH"], "hello-world.md"), "r") as r:
                body = r.read()
            category = Category(category="demo", is_show=False)
            tag = Tag(tag="demo")
            post = Post(
                title="hello world",
                url_name="helloworld",
                create_time=nowstr(fmt="%Y-%m-%d"),
                body=body,
                tags="demo",
                category=category
            )
            db.session.add(category)
            db.session.add(tag)
            db.session.add(post)
        db.session.commit()

    @app.cli.command()
    @click.option("--clear_alembic", default=True, help="Create after drop.")
    def clear_alembic():
        from yublog.models import Alembic
        Alembic.clear()


def _global_data():
    """全局缓存"""
    global_data = {}
    typ = CacheType.GLOBAL

    caches = cache_operate.get_many(typ, *[
        CacheKey.ADMIN,
        CacheKey.SOCIAL_LINKS,
        CacheKey.FRIEND_COUNT,
        CacheKey.TAGS,
        CacheKey.CATEGORIES,
        CacheKey.PAGES,
        CacheKey.LOVE_COUNT,
        CacheKey.POST_COUNT,
        CacheKey.LAST_TALK,
        CacheKey.GUEST_BOOK_COUNT,
        CacheKey.ADS_BOXES,
        CacheKey.SITE_BOXES,
    ])
    (
        c_admin,
        c_social,
        c_friend_count,
        c_tags,
        c_categories,
        c_pages,
        c_love_me_counts,
        c_posts,
        c_talk,
        c_guest_book_count,
        c_adv_boxes,
        c_site_boxes
    ) = caches

    def _admin():
        admin = Admin.query.first()
        if admin is None:
            abort(404)
            raise AppInitException("no Admin")

        cache_operate.set(typ, CacheKey.ADMIN, admin)
        return admin

    def _links():
        if c_social and c_friend_count:
            return c_social, c_friend_count

        ls = Link.query.order_by(Link.id.desc()).all()
        social = [link for link in ls if link.is_friend is False]
        friend_count = len(ls) - len(social)

        cache_operate.set(typ, CacheKey.SOCIAL_LINKS, social)
        cache_operate.set(typ, CacheKey.FRIEND_COUNT, friend_count)
        return social, friend_count

    def _tags():
        ts = Tag.query.all()
        cache_operate.set(typ, CacheKey.TAGS, ts)
        return ts

    def _categories():
        cs = Category.query.filter_by(is_show=True).all()
        cache_operate.set(typ, CacheKey.CATEGORIES, cs)
        return cs

    def _pages():
        ps = Page.query.filter_by(show_nav=True).all()
        cache_operate.set(typ, CacheKey.PAGES, ps)
        return ps

    def _love_me_counts():
        lc = LoveMe.query.first()
        if lc is None:
            abort(404)
            raise AppInitException("no LoveMe")

        count = lc.count
        cache_operate.set(typ, CacheKey.LOVE_COUNT, count)
        return count

    def _posts():
        ps = Post.query.filter_by(draft=False).count()
        cache_operate.set(typ, CacheKey.POST_COUNT, ps)
        return ps

    def _talk():
        t = Talk.query.order_by(Talk.timestamp.desc()).first()
        body = t.body_to_html if t else ""
        cache_operate.set(typ, CacheKey.LAST_TALK, body)
        return body

    def _guest_book():
        p = Page.query.filter_by(url_name="guest-book").first()
        count = p.comments.filter_by(disabled=True).count() if p and p.comments else 0
        cache_operate.set(typ, CacheKey.GUEST_BOOK_COUNT, count)
        return count

    def _boxes():
        if c_adv_boxes and c_site_boxes:
            return c_adv_boxes, c_site_boxes

        bs = SideBox.query.order_by(SideBox.id.desc()).all()
        adv = [box for box in bs if not box.unable and box.is_advertising]
        site = [box for box in bs if not (box.unable or box.is_advertising)]

        cache_operate.set(typ, CacheKey.ADS_BOXES, adv)
        cache_operate.set(typ, CacheKey.SITE_BOXES, site)
        return adv, site

    social_links, friend_links_counts = _links()
    guest_book = c_guest_book_count or _guest_book()
    adv_boxes, site_boxes = _boxes()

    global_data[CacheKey.ADMIN] = c_admin or _admin()
    global_data[CacheKey.TAGS] = c_tags or _tags()
    global_data[CacheKey.CATEGORIES] = c_categories or _categories()
    global_data[CacheKey.PAGES] = c_pages or _pages()
    global_data[CacheKey.LOVE_COUNT] = c_love_me_counts or _love_me_counts()
    global_data[CacheKey.POST_COUNT] = c_posts or _posts()
    global_data[CacheKey.LAST_TALK] = c_talk or _talk()
    global_data[CacheKey.GUEST_BOOK_COUNT] = guest_book
    global_data[CacheKey.SOCIAL_LINKS] = social_links
    global_data[CacheKey.FRIEND_COUNT] = friend_links_counts
    global_data[CacheKey.ADS_BOXES] = adv_boxes
    global_data[CacheKey.SITE_BOXES] = site_boxes

    return global_data


@main_bp.app_context_processor
@log_time
def app_global_data():
    return cache_operate.getset(
        CacheType.GLOBAL,
        CacheKey.GLOBAL,
        callback=_global_data,
        timeout=1
    )


@main_bp.before_request
def before_first_request():
    g.search_form = SearchForm()
    g.search_form2 = MobileSearchForm()


def register_template_filter(app):
    @app.template_filter("local_image")
    def local_image_filter(html):
        # <img alt="post41_1" src="/image/post41/post41_1.png">
        # ![post41_1](/image/post41/post41_1.png)
        pass
