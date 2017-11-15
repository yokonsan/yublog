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
    name = db.Column(db.String)
    profile = db.Column(db.String)
    login_name = db.Column(db.String)
    password = db.Column(db.String)

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

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    url_name = db.Column(db.DateTime)
    body = db.Column(db.Text)
    datetime = db.Column(db.String)
    disabled = db.Column(db.Boolean)
    view_num = db.Column(db.Integer, default=0)
    body_html = db.Column(db.Text)
    draft = db.Column(db.Boolean, default=False)

    tags = db.relationship('Tag', backref='post', lazy='dynamic')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref='post', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)

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
    tag = db.Column(db.String, index=True)
    datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def __init__(self, tag, datetime, post_id):
        self.tag = tag
        self.datetime = datetime
        self.post_id = post_id

    def __repr__(self):
        return '<Tag %r>' % (self.tag)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String, index=True)
    datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def __init__(self, category, datetime):
        self.category = category
        self.datetime = datetime

    def __repr__(self):
        return '<Category %r>' % (self.category)

class SocialLink(db.Model):
    __tablename__ = 'social_links'
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String)
    isFriendLink = db.Column(db.Boolean)

    def __init__(self, link, isFriendLink):
        self.link = link
        self.isFriendLink = isFriendLink

    def __repr__(self):
        return '<SocialLink %r>' % (self.link)

