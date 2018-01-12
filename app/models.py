import datetime
from hashlib import md5

import bleach
from flask_login import UserMixin
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, lm, whooshee


class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(4))
    site_title = db.Column(db.String(255))
    name = db.Column(db.String(4))
    profile = db.Column(db.String(255))
    login_name = db.Column(db.String(500))
    password_hash = db.Column(db.String(500))

    record_info = db.Column(db.String(255), nullable=True)

    def __init__(self, **kwargs):
        super(Admin, self).__init__(**kwargs)

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

@lm.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

class LoveMe(db.Model):
    __tablename__ = 'loveme'
    id = db.Column(db.Integer, primary_key=True)
    loveMe = db.Column(db.Integer, default=666)

    def __init__(self, loveMe):
        self.loveMe = loveMe

    def __repr__(self):
        return '<LoveMe %r>' % (self.loveMe)

class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(3))
    url_name = db.Column(db.String(25))
    canComment = db.Column(db.Boolean, default=False)
    isNav = db.Column(db.Boolean, default=False)
    body = db.Column(db.Text)

    comments = db.relationship('Comment', backref='page', lazy='dynamic')

    @property
    def body_to_html(self):
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'img', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2',
            'h3', 'p'
        ]
        body_html = bleach.linkify(bleach.clean(
            markdown(self.body, output_format='html'),
            tags=allowed_tags, strip=True,
            attributes={
                '*': ['class'],
                'a': ['href', 'rel'],
                'img': ['src', 'alt'],  # 支持标签和属性
            }
        ))
        return body_html

    def __repr__(self):
        return '<Page %r>' % (self.title)

@whooshee.register_model('title', 'body')
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    url_name = db.Column(db.String(64))
    timestamp = db.Column(db.String(64))
    view_num = db.Column(db.Integer, default=0)
    body = db.Column(db.Text)
    draft = db.Column(db.Boolean, default=False)
    disable = db.Column(db.Boolean, default=False)

    tags = db.Column(db.String(64))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @property
    def timestampInt(self):
        return int(''.join([i for i in self.timestamp.split('-')]))
    @property
    def year(self):
        return int([i for i in self.timestamp.split('-')][0])
    @property
    def month(self):
        return int([i for i in self.timestamp.split('-')][1])

    def tag_in_post(self, tag):
        try:
            tags = [i for i in self.tags.split(',')]
            if tag in tags:
                return True
            return False
        except:
            if tag == self.tags:
                return True
            return False

    @property
    def body_to_html(self):
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'img', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2',
            'h3', 'p'
        ]
        body_html = bleach.linkify(bleach.clean(
            markdown(self.body, output_format='html'),
            tags=allowed_tags, strip=True,
            attributes={
                '*': ['class'],
                'a': ['href', 'rel'],
                'img': ['src', 'alt'],  # 支持标签和属性
            }
        ))
        return body_html

    def __repr__(self):
        return '<Post %r>' % (self.title)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)
    author = db.Column(db.String(25))
    email = db.Column(db.String(255))
    website = db.Column(db.String(255), nullable=True)
    isReply = db.Column(db.Boolean, default=False)
    replyTo = db.Column(db.Integer, nullable=True)
    disabled = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)

    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'))

    @property
    def strptime(self):
        return datetime.datetime.strftime(self.timestamp, '%Y-%m-%d')

    # 获取Gravatar头像
    def gravatar(self, size):
        return 'http://www.gravatar.com/avatar/' + md5(self.email.encode('utf-8')).hexdigest() + '?d=mm&s=' + str(size)

    def __repr__(self):
        return '<Comment %r>' %(self.comment)

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(6), index=True)

    def __repr__(self):
        return '<Tag %r>' % (self.tag)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(6), index=True)

    posts = db.relationship('Post', backref='category')

    def __repr__(self):
        return '<Category %r>' % (self.category)

class SiteLink(db.Model):
    __tablename__ = 'sitelinks'
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(125))
    name = db.Column(db.String(25))
    isFriendLink = db.Column(db.Boolean)
    isGreatLink = db.Column(db.Boolean, default=True)
    info = db.Column(db.String(125), nullable=True)

    def __repr__(self):
        return '<SiteLink %r>' % (self.link)

class Shuoshuo(db.Model):
    __tablename__ = 'shuos'
    id = db.Column(db.Integer, primary_key=True)
    shuo = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)

    def __init__(self, shuo):
        self.shuo = shuo

    @property
    def strptime(self):
        return datetime.datetime.strftime(self.timestamp, '%Y-%m-%d')
    @property
    def year(self):
        return int([i for i in self.strptime.split('-')][0])
    @property
    def month_and_day(self):
        return [i for i in self.strptime.split('-')][1] + '/' + [i for i in self.strptime.split('-')][2]

    @property
    def body_to_html(self):
        allowed_tags = [
            'a', 'abbr', 'acronym', 'b', 'img', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2',
            'h3', 'p'
        ]
        body_html = bleach.linkify(bleach.clean(
            markdown(self.shuo, output_format='html'),
            tags=allowed_tags, strip=True,
            attributes={
                '*': ['class'],
                'a': ['href', 'rel'],
                'img': ['src', 'alt'],  # 支持标签和属性
            }
        ))
        return body_html

    def __repr__(self):
        return '<Shuoshuo %r>' % (self.shuo)


class Alembic(db.Model):
    __tablename__ = 'alembic_version'
    version_num = db.Column(db.String(32), primary_key=True, nullable=False)

    @staticmethod
    def clear_A():
        for a in Alembic.query.all():
            db.session.delete(a)
        db.session.commit()
