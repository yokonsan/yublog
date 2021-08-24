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
        return '<Admin name: {}>'.format(self.name)


class LoveMe(db.Model):
    """站点喜欢按钮次数数据模型"""
    __tablename__ = 'loveme'
    id = db.Column(db.Integer, primary_key=True)
    love_count = db.Column(db.Integer, default=0)

    def __init__(self, love_me_count):
        self.love_count = love_me_count

    def __repr__(self):
        return '<Love me count: {}>'.format(self.love_count)


class Page(db.Model):
    """站点页面数据模型"""
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(6))
    url_name = db.Column(db.String(25), unique=True)
    able_comment = db.Column(db.Boolean, default=False)
    show_nav = db.Column(db.Boolean, default=False, index=True)
    body = db.Column(db.Text)

    comments = db.relationship('Comment', backref='page', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Page, self).__init__(**kwargs)

    @property
    def body_to_html(self):
        html = markdown_to_html(self.body)
        return html

    def to_json(self):
        page = {
            'id': self.id,
            'title': self.title,
            'url': self.url_name,
            'api': url_for('api.get_page', id=self.id, _external=True),
            'show_nav': self.show_nav,
            'comment_count': self.comments.count() if self.able_comment else None,
            'comments': url_for('api.get_page_comments', id=self.id, _external=True) \
                if self.able_comment else None
        }
        return page

    def __repr__(self):
        return '<Page name: {}>'.format(self.title)


@whooshee.register_model('title', 'body')
class Post(db.Model):
    """为了把文章缓存时间久一些，把文章浏览量模型分离"""
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    url_name = db.Column(db.String(64), unique=True)
    timestamp = db.Column(db.String(64), index=True)
    body = db.Column(db.Text)
    draft = db.Column(db.Boolean, default=False, index=True)
    disable = db.Column(db.Boolean, default=False, index=True)

    tags = db.Column(db.String(64))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    @property
    def timestamp_int(self):
        return int(self.timestamp.replace('-', ''))

    @property
    def year(self):
        return int(self.timestamp.split('-')[0])

    @property
    def month(self):
        return int(self.timestamp.split('-')[1])

    @property
    def body_to_html(self):
        html = markdown_to_html(self.body)
        return html

    def tag_in_post(self, tag):
        if self.tags.find(',') > -1:
            return tag in self.tags.split(',')

        return tag == self.tags

    def to_json(self):
        post = {
            'id': self.id,
            'title': self.title,
            'api': url_for('api.get_post', id=self.id, _external=True),
            'datetime': self.timestamp,
            'category': self.category.category,
            'tag': self.tags,
            'comment_count': self.comments.filter_by(disabled=True).count(),
            'comments': url_for('api.get_post_comments', id=self.id, _external=True)  # noqa
        }
        return post

    def to_dict(self):
        """缓存"""
        post = {
            'id': self.id,
            'url': self.url_name,
            'title': self.title,
            'body': self.body_to_html,
            'year': self.year,
            'month': self.month,
            'datetime': self.timestamp,
            'category': self.category.category,
            'tag': self.tags,
            'comment_count': self.comments.filter_by(disabled=True).count()
        }
        return post

    def __repr__(self):
        return '<Post title: {}>'.format(self.title)


class View(db.Model):
    """文章浏览量数据模型"""
    __tablename__ = 'views'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)
    type = db.Column(db.String(25), default='post', index=True)

    relationship_id = db.Column(db.Integer, index=True)

    def __repr__(self):
        return '<View count: {}>'.format(self.count)


class Comment(db.Model):
    """
    评论数据模型
    增加 type 键｛
        'post': 博客文章评论
        'page': 博客页面评论
        'article': 专栏文章评论
    ｝
    以type和id来获取对于评论
    """
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)
    author = db.Column(db.String(25))
    email = db.Column(db.String(255))
    website = db.Column(db.String(255), nullable=True)
    disabled = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)  # noqa

    replies = db.relationship('Comment', back_populates='replied', cascade='all, delete-orphan')  # noqa
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id])  # noqa
    replied_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    page_id = db.Column(db.Integer, db.ForeignKey('pages.id'))
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))

    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)
        if self.website and not(self.website.startswith('http://') or self.website.startswith('https://')):
            self.website = 'http://{}'.format(self.website)

    @property
    def strptime(self):
        return datetime.datetime.strftime(self.timestamp, '%Y-%m-%d')

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
        return 'http://www.gravatar.com/avatar/{0}?d=mm&s={1}'.format(
            md5(self.email.encode('utf-8')).hexdigest(), str(size))

    def to_json(self):
        comment = {
            'id': self.id,
            'author': self.author,
            'avatar': self.gravatar(38),
            'mail': self.email,
            'site': self.website,
            'datetime': self.strptime,
            'comment': self.body_to_html
        }
        if self.replied_id:
            comment['avatar'] = self.gravatar(26)
            comment['reply_to'] = self.replied_id
        return comment

    def __repr__(self):
        return '<Comment body: {}>'.format(self.comment)


class Tag(db.Model):
    """标签数据模型"""
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(25), index=True, unique=True)
    is_show = db.Column(db.Boolean, default=True, index=True)

    def to_json(self):
        tag = {
            'tag': self.tag,
            'posts': url_for('api.get_tag_posts', tag=self.tag, _external=True)
        }
        return tag

    def __repr__(self):
        return '<Tag name: {}>'.format(self.tag)


class Category(db.Model):
    """分类数据模型"""
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(6), index=True, unique=True)
    is_show = db.Column(db.Boolean, default=True, index=True)

    posts = db.relationship('Post', backref='category', lazy='dynamic')

    def to_json(self):
        category = {
            'category': self.category,
            'post_count': self.posts.count(),
            'posts': url_for('api.get_category_posts', category=self.category, _external=True)  # noqa
        }
        return category

    def __repr__(self):
        return '<Category name: {}>'.format(self.category)


class SiteLink(db.Model):
    """站点链接数据模型"""
    __tablename__ = 'sitelinks'
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(125), unique=True)
    name = db.Column(db.String(25))
    is_friend = db.Column(db.Boolean, index=True)
    is_great = db.Column(db.Boolean, default=True, index=True)
    info = db.Column(db.String(125), nullable=True)

    def __repr__(self):
        return '<Site link: {}>'.format(self.link)


class Talk(db.Model):
    """说说数据模型"""
    __tablename__ = 'talk'
    id = db.Column(db.Integer, primary_key=True)
    talk = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.now)  # noqa

    def __init__(self, talk):
        self.talk = talk

    @property
    def strptime(self):
        return datetime.datetime.strftime(self.timestamp, '%Y-%m-%d')

    @property
    def year(self):
        return int(self.strptime.split('-')[0])

    @property
    def month_and_day(self):
        return '/'.join(self.strptime.split('-')[1:])

    @property
    def body_to_html(self):
        html = markdown_to_html(self.talk)
        return html

    def to_json(self):
        shuo = {
            'talk': self.talk,
            'datetime': self.strptime
        }
        return shuo

    def __repr__(self):
        return '<Talk body: {}>'.format(self.talk)


class Column(db.Model):
    """专栏数据模型"""
    __tablename__ = 'columns'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    url_name = db.Column(db.String(64), unique=True, index=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.String(64))
    password_hash = db.Column(db.String(500))

    articles = db.relationship('Article', backref='column', lazy='dynamic')

    @property
    def body_to_html(self):
        html = markdown_to_html(self.body)
        return html

    # 对密码进行加密保存
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password) if password else None  # noqa

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        column = {
            'id': self.id,
            'title': self.title,
            'body': self.body_to_html,
            'timestamp': self.timestamp,
            'url_name': self.url_name,
            'password_hash': self.password_hash,
            'articles': []
        }
        return column

    def __repr__(self):
        return '<Column name: {}>'.format(self.title)


class Article(db.Model):
    """专栏文章数据模型"""
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    body = db.Column(db.Text)
    secrecy = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.String(64))

    column_id = db.Column(db.Integer, db.ForeignKey('columns.id'))
    comments = db.relationship('Comment', backref='article', lazy='dynamic')

    @property
    def body_to_html(self):
        html = markdown_to_html(self.body)
        return html

    def to_dict(self):
        article = {
            'id': self.id,
            'title': self.title,
            'body': self.body_to_html,
            'secrecy': self.secrecy,
            'timestamp': self.timestamp,
            'column': self.column.title,
            'comment_count': self.comments.count()
        }
        return article

    def __repr__(self):
        return '<Article title: {}>'.format(self.title)


class SideBox(db.Model):
    """站点侧栏数据模型"""
    __tablename__ = 'side_boxes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=True, unique=True)
    body = db.Column(db.Text)
    unable = db.Column(db.Boolean, default=False)
    is_advertising = db.Column(db.Boolean)

    def __repr__(self):
        return '<Side box title: {}>'.format(self.title)


class ImagePath(db.Model):
    __tablename__ = 'image_path'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(64), nullable=False, unique=True, index=True)

    images = db.relationship('Image', backref='image_path', lazy='dynamic')


class Image(db.Model):
    __tablename__ = 'image'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

    path = db.Column(db.String(64), db.ForeignKey('image_path.path'))


class Alembic(db.Model):
    __tablename__ = 'alembic_version'
    version_num = db.Column(db.String(32), primary_key=True, nullable=False)

    @staticmethod
    def clear():
        for a in Alembic.query.all():
            db.session.delete(a)
        db.session.commit()
