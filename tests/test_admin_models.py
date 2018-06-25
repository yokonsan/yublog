import unittest

from flask import current_app

from app import create_app, db
from app.models import Post, Page, Admin, Comment, Column, Article, \
        Category, Tag, Shuoshuo, SiteLink, SideBox, LoveMe


class AdminTestCase(unittest.TestCase):
    """测试管理员数据库模型"""

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_tourists_login(self):
        """非管理员登录后台"""
        user = Admin.query.filter_by(login_name='tourists').first()
        self.assertIsNone(user)

    def test_admin_login(self):
        """管理员登录"""
        _login_name = current_app.config['ADMIN_LOGIN_NAME']
        _password = current_app.config['ADMIN_PASSWORD']
        user = Admin.query.filter_by(login_name=_login_name).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.verify_password(_password))

    def test_add_article(self):
        """添加文章"""
        category = Category.query.filter_by(category='test').first()
        if not category:
            category = Category(category='test')
            db.session.add(category)

        tags = [tag for tag in 'test,flask'.split(',')]
        test_post = Post(body='This is a test post.', title='test',
                    url_name='test-post', category=category,
                    tags='test,flask', timestamp='2018-08-18', draft=False)
        for tag in tags:
            exist_tag = Tag.query.filter_by(tag=tag).first()
            if not exist_tag:
                tag = Tag(tag=tag)
                db.session.add(tag)
        db.session.add(test_post)
        db.session.commit()
        post = Post.query.filter_by(title='test').first()
        self.assertIsNotNone(post)

    def test_add_page(self):
        """添加页面"""
        test_page = Page(title='test',
                    url_name='test-page',
                    body='This is a test page.',
                    canComment=False,
                    isNav=False)
        db.session.add(test_page)
        db.session.commit()
        page = Page.query.filter_by(title='test').first()
        self.assertIsNotNone(page)

    def test_add_shuoshuo(self):
        """添加说说"""
        test_shuo = Shuoshuo(shuo='This a test shuoshuo.')
        db.session.add(test_shuo)
        db.session.commit()
        shuo = Shuoshuo.query.filter_by(shuo='This a test shuoshuo.').first()
        self.assertIsNotNone(shuo)

    def test_add_link(self):
        """添加链接"""
        test_social_link = SiteLink(link='http://www.baidu.com', name='baidu',
                        isFriendLink=False)
        db.session.add(test_social_link)
        test_friend_link = SiteLink(link='http://www.yukunweb.com', name='yukun',
                        info='This is a friend link.', isFriendLink=True)
        db.session.add(test_friend_link)
        db.session.commit()
        exist_link = SiteLink.query.filter_by(link='http://www.yukunweb.com').first()
        not_exist_link = SiteLink.query.filter_by(link='http://www.test.com').first()
        self.assertIsNotNone(exist_link)
        self.assertIsNone(not_exist_link)

    def test_add_column(self):
        """添加专题"""
        test_column = Column(column='test', timestamp='2018-08-18',
                        url_name='test-column', body='This is a test column.')
        db.session.add(test_column)
        db.session.commit()
        column = Column.query.filter_by(column='test').first()
        self.assertIsNotNone(column)

    def test_add_column_article(self):
        """添加专栏文章"""
        column = Column.query.filter_by(url_name='test-column').first()
        test_article = Article(title='test-article', timestamp='2018-08-18',
                          body='This is a test article.', secrecy=False, column=column)
        db.session.add(test_article)
        db.session.commit()
        article = Article.query.filter_by(title='test-article').first()
        self.assertIsNotNone(article)

    def test_add_plugin(self):
        """添加插件"""
        test_box = SideBox(title='test-box', body='This is a test box.',
                      is_advertising=False)
        db.session.add(test_box)
        db.session.commit()
        box = SideBox(title='test-box')
        self.assertIsNotNone(box)


