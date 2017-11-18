import datetime
import bleach
from flask_login import UserMixin
from flask import current_app
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, lm


class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(4))
    name = db.Column(db.String(4))
    profile = db.Column(db.String(16))
    login_name = db.Column(db.String(4))
    password = db.Column(db.String(16))

    def __init__(self, name, login_name, password):
        self.name = name
        self.login_name = login_name
        self.password = password

    # 对密码进行加密保存
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Admin %r>' % (self.name)

class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(3))
    url_name = db.Column(db.String(25))
    canComment = db.Column(db.Boolean, default=False)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)

    def __init__(self, page, body, body_html, canComment, url_name, timestamp):
        self.page = page
        self.body = body
        self.body_html = body_html
        self.canComment = canComment
        self.url_name = url_name
        self.timestamp = timestamp


    def __repr__(self):
        return '<Page %r>' % (self.page)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    url_name = db.Column(db.DateTime)
    body = db.Column(db.Text)
    timestamp = db.Column(db.Integer)
    view_num = db.Column(db.Integer, default=0)
    body_html = db.Column(db.Text)
    draft = db.Column(db.Boolean, default=False)

    tags = db.relationship('Tag', backref='post', lazy='dynamic')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref='post', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)

    @staticmethod
    def tag_in_post(self, tag):
        if tag in self.tags:
            return True
        return False

    @staticmethod
    def change_body(target, value, oldvalue, initiator):
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'img', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2',
            'h3', 'p'
        ]
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True,
            attributes={
                '*': ['class'],
                'a': ['href', 'rel'],
                'img': ['src', 'alt'],  # 支持标签和属性
            }
        ))

    def __repr__(self):
        return '<Post %r>' % (self.title)

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(6), index=True)
    url_name = db.Column(db.String(25))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def __init__(self, tag, timestamp, post_id, url_name):
        self.tag = tag
        self.timestamp = timestamp
        self.post_id = post_id
        self.url_name = url_name

    def __repr__(self):
        return '<Tag %r>' % (self.tag)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(6), index=True)
    url_name = db.Column(db.String(16))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def __init__(self, category, timestamp, url_name):
        self.category = category
        self.timestamp = timestamp
        self.url_name = url_name

    def __repr__(self):
        return '<Category %r>' % (self.category)

class SocialLink(db.Model):
    __tablename__ = 'social_links'
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(125))
    name = db.Column(db.String(25))
    isFriendLink = db.Column(db.Boolean)

    def __init__(self, link, isFriendLink, name):
        self.link = link
        self.isFriendLink = isFriendLink
        self.name = name

    def __repr__(self):
        return '<SocialLink %r>' % (self.link)

