import datetime
from hashlib import md5

from flask import url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from yublog import db, whooshee
from yublog.utils.tools import markdown_to_html
from yublog.utils.pxfilter import XssHtml


class Admin(UserMixin, db.Model):
    """管理员数据模型"""
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(10))
    site_title = db.Column(db.String(255))
    name = db.Column(db.String(10), unique=True)
    profile = db.Column(db.String(255))
    login_name = db.Column(db.String(500))
    password_hash = db.Column(db.String(500))

    record_info = db.Column(db.String(255), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Admin name: {self.name}>"


class LoveMe(db.Model):
    """站点喜欢按钮次数数据模型"""
    __tablename__ = "loveme"
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Love me count: {self.count}>"


class Page(db.Model):
    """站点页面数据模型"""
    __tablename__ = "page"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(10))
    url_name = db.Column(db.String(25), unique=True)
    enable_comment = db.Column(db.Boolean, default=False)
    show_nav = db.Column(db.Boolean, default=False, index=True)
    body = db.Column(db.Text)

    comments = db.relationship("Comment", backref="page", lazy="dynamic")

    @property
    def body_to_html(self):
        html = markdown_to_html(self.body)
        return html

    def to_json(self):
        page = {
            "id": self.id,
            "title": self.title,
            "url": self.url_name,
            "api": url_for("api.get_page", id=self.id, _external=True),
            "show_nav": self.show_nav,
            "comment_count": self.comments.count() if self.enable_comment else None,
            "comments": url_for("api.get_page_comments", id=self.id, _external=True) if self.enable_comment else None
        }
        return page

    def __repr__(self):
        return f"<Page name: {self.title}>"


@whooshee.register_model("title", "body")
class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    url_name = db.Column(db.String(64), unique=True)
    create_time = db.Column(db.String(64), index=True)
    body = db.Column(db.Text)
    draft = db.Column(db.Boolean, default=False, index=True)
    disable = db.Column(db.Boolean, default=False, index=True)

    tags = db.Column(db.String(64))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    comments = db.relationship("Comment", backref="post", lazy="dynamic")

    @property
    def year(self):
        return int(self.create_time.split("-")[0])

    @property
    def month(self):
        return int(self.create_time.split("-")[1])

    @property
    def body_to_html(self):
        html = markdown_to_html(self.body)
        return html

    def tag_in_post(self, tag):
        if self.tags.find(",") > -1:
            return tag in self.tags.split(",")

        return tag == self.tags

    def to_json(self):
        post = {
            "id": self.id,
            "title": self.title,
            "api": url_for("api.get_post", id=self.id, _external=True),
            "datetime": self.create_time,
            "category": self.category.category,
            "tag": self.tags,
            "comment_count": self.comments.filter_by(disabled=True).count(),
            "comments": url_for("api.get_post_comments", id=self.id, _external=True)  # noqa
        }
        return post

    def to_dict(self):
        """缓存"""
        post = {
            "id": self.id,
            "url": self.url_name,
            "title": self.title,
            "body": self.body_to_html,
            "year": self.year,
            "month": self.month,
            "datetime": self.create_time,
            "category": self.category.category,
            "tag": self.tags,
            "comment_count": self.comments.filter_by(disabled=True).count()
        }
        return post

    def __repr__(self):
        return f"<Post title: {self.title}>"


class View(db.Model):
    """文章浏览量数据模型"""
    __tablename__ = "view"
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)
    type = db.Column(db.String(25), default="post", index=True)

    relationship_id = db.Column(db.Integer, index=True)

    def __repr__(self):
        return f"<View count: {self.count}>"


class Comment(db.Model):
    """
    评论数据模型
    增加 type 键｛
        "post": 博客文章评论
        "page": 博客页面评论
        "article": 专栏文章评论
    ｝
    以type和id来获取对于评论
    """
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)
    author = db.Column(db.String(25))
    email = db.Column(db.String(255))
    website = db.Column(db.String(255), nullable=True)
    disabled = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)  # noqa

    replies = db.relationship("Comment", back_populates="replied", cascade="all, delete-orphan")  # noqa
    replied = db.relationship("Comment", back_populates="replies", remote_side=[id])  # noqa
    replied_id = db.Column(db.Integer, db.ForeignKey("comment.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    page_id = db.Column(db.Integer, db.ForeignKey("page.id"))
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"))

    @property
    def strptime(self):
        return datetime.datetime.strftime(self.timestamp, "%Y-%m-%d")

    @property
    def body_to_html(self):
        # xss过滤
        html = markdown_to_html(self.comment)

        parser = XssHtml()
        parser.feed(html)
        parser.close()
        return parser.get_html()

    # 获取 Gravatar 头像
    def gravatar(self, size):
        return f"http://www.gravatar.com/avatar/{md5(self.email.encode('utf-8')).hexdigest()}?d=mm&s={size}"

    def to_json(self):
        comment = {
            "id": self.id,
            "author": self.author,
            "avatar": self.gravatar(38),
            "mail": self.email,
            "site": self.website,
            "datetime": self.strptime,
            "comment": self.body_to_html
        }
        if self.replied_id:
            comment["avatar"] = self.gravatar(26)
            comment["reply_to"] = self.replied_id
        return comment

    def __repr__(self):
        return f"<Comment body: {self.comment}>"


class Tag(db.Model):
    """标签数据模型"""
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(25), index=True, unique=True)
    is_show = db.Column(db.Boolean, default=True, index=True)

    def to_json(self):
        tag = {
            "tag": self.tag,
            "posts": url_for("api.get_tag_posts", tag=self.tag, _external=True)
        }
        return tag

    def __repr__(self):
        return f"<Tag name: {self.tag}>"


class Category(db.Model):
    """分类数据模型"""
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(6), index=True, unique=True)
    is_show = db.Column(db.Boolean, default=True, index=True)

    posts = db.relationship("Post", backref="category", lazy="dynamic")

    def to_json(self):
        category = {
            "category": self.category,
            "post_count": self.posts.count(),
            "posts": url_for("api.get_category_posts", category=self.category, _external=True)  # noqa
        }
        return category

    def __repr__(self):
        return f"<Category name: {self.category}>"


class Link(db.Model):
    """站点链接数据模型"""
    __tablename__ = "link"
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(125), unique=True)
    name = db.Column(db.String(25))
    is_friend = db.Column(db.Boolean, index=True)
    is_great = db.Column(db.Boolean, default=True, index=True)
    info = db.Column(db.String(125), nullable=True)

    def __repr__(self):
        return f"<Link: {self.link}>"


class Talk(db.Model):
    """说说数据模型"""
    __tablename__ = "talk"
    id = db.Column(db.Integer, primary_key=True)
    talk = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)  # noqa

    # def __init__(self, talk):
    #     self.talk = talk

    @property
    def strptime(self):
        return datetime.datetime.strftime(self.timestamp, "%Y-%m-%d")

    @property
    def year(self):
        return int(self.strptime.split("-")[0])

    @property
    def month_and_day(self):
        return "/".join(self.strptime.split("-")[1:])

    @property
    def body_to_html(self):
        html = markdown_to_html(self.talk)
        return html

    def to_json(self):
        shuo = {
            "talk": self.talk,
            "datetime": self.strptime
        }
        return shuo

    def __repr__(self):
        return f"<Talk body: {self.talk}>"


class Column(db.Model):
    """专栏数据模型"""
    __tablename__ = "column"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    url_name = db.Column(db.String(64), unique=True, index=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.String(64))
    password_hash = db.Column(db.String(500))

    articles = db.relationship("Article", backref="column", lazy="dynamic")

    @property
    def body_to_html(self):
        html = markdown_to_html(self.body)
        return html

    # 对密码进行加密保存
    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password) if password else None  # noqa

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        column = {
            "id": self.id,
            "title": self.title,
            "body": self.body_to_html,
            "timestamp": self.timestamp,
            "url_name": self.url_name,
            "password_hash": self.password_hash,
            "articles": []
        }
        return column

    def __repr__(self):
        return f"<Column name: {self.title}>"


class Article(db.Model):
    """专栏文章数据模型"""
    __tablename__ = "article"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    body = db.Column(db.Text)
    secrecy = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.String(64))

    column_id = db.Column(db.Integer, db.ForeignKey("column.id"))
    comments = db.relationship("Comment", backref="article", lazy="dynamic")

    @property
    def body_to_html(self):
        html = markdown_to_html(self.body)
        return html

    def to_dict(self):
        article = {
            "id": self.id,
            "title": self.title,
            "body": self.body_to_html,
            "secrecy": self.secrecy,
            "timestamp": self.timestamp,
            "column": self.column.title,
            "comment_count": self.comments.count()
        }
        return article

    def __repr__(self):
        return f"<Article title: {self.title}>"


class SideBox(db.Model):
    """站点侧栏数据模型"""
    __tablename__ = "side_box"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=True, unique=True)
    body = db.Column(db.Text)
    unable = db.Column(db.Boolean, default=False)
    is_advertising = db.Column(db.Boolean)

    def __repr__(self):
        return f"<Side box title: {self.title}>"


class ImagePath(db.Model):
    __tablename__ = "image_path"
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(64), nullable=False, unique=True, index=True)

    images = db.relationship("Image", backref="image_path", lazy="dynamic")


class Image(db.Model):
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

    path = db.Column(db.String(64), db.ForeignKey("image_path.path"))


class Alembic(db.Model):
    __tablename__ = "alembic_version"
    version_num = db.Column(db.String(32), primary_key=True, nullable=False)

    @staticmethod
    def clear():
        for a in Alembic.query.all():
            db.session.delete(a)
        db.session.commit()
