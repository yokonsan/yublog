import unittest

from flask import current_app

from app import create_app, db
from app.models import Post, Page, Admin, Column, Article, \
        Category, Tag, Shuoshuo, SiteLink, SideBox


class AdminTestCase(unittest.TestCase):
    """测试管理员数据库模型"""

    # def setUp(self):
    #     self.app = create_app('testing')
    #     self.app_context = self.app.app_context()
    #     self.app_context.push()
    #     db.create_all()
    #     print('start')

    # def tearDown(self):
    #     db.session.remove()
    #     db.drop_all()
    #     self.app_context.pop()
    # def test_create_app
    def test_init(self):
        """初始化"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def test_end(self):
        """结束清理"""
        db.session.remove()
        db.drop_all()

    def test_add_admin(self):
        """添加管理员"""
        admin = Admin(site_name=current_app.config['SITE_NAME'], site_title=current_app.config['SITE_TITLE'],
                      name=current_app.config['ADMIN_NAME'], profile=current_app.config['ADMIN_PROFILE'],
                      login_name=current_app.config['ADMIN_LOGIN_NAME'], password=current_app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        db.session.commit()
        test_user = Admin.query.all()
        self.assertIsNotNone(test_user[0])

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
        # for tag in tags:
        #     exist_tag = Tag.query.filter_by(tag=tag).first()
        #     if not exist_tag:
        #         tag = Tag(tag=tag)
        #         db.session.add(tag)
        db.session.add(test_post)
        db.session.commit()
        post = Post.query.filter_by(title='test').first()
        self.assertIsNotNone(post)

    def test_add_page(self):
        """添加页面"""
        test_page = Page(title='test', url_name='test-page',
                         body='This is a test page.', canComment=False, isNav=False)
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
        box = SideBox.query.filter_by(title='test-box').first()
        self.assertIsNotNone(box)

    def test_admin_post(self):
        """管理文章"""
        test_post = Post.query.filter_by(title='test').first()
        test_post.title = 'test_admin'
        db.session.add(test_post)
        db.session.commit()
        post = Post.query.filter_by(url_name='test-post').first()
        self.assertEqual(post.title, 'test_admin')

    def test_delete_post(self):
        """删除文章"""
        test_post = Post.query.filter_by(url_name='test-post').first()
        db.session.delete(test_post)
        db.session.commit()
        post = Post.query.filter_by(url_name='test-post').first()
        self.assertIsNone(post)

    def test_admin_page(self):
        """管理页面"""
        test_page = Page.query.filter_by(title='test').first()
        test_page.title = 'admin'
        db.session.add(test_page)
        db.session.commit()
        page = Page.query.filter_by(url_name='test-page').first()
        self.assertEqual(page.title, 'admin')

    def test_delete_page(self):
        """删除页面"""
        test_page = Page.query.filter_by(url_name='test-page').first()
        db.session.delete(test_page)
        db.session.commit()
        page = Post.query.filter_by(url_name='test-page').first()
        self.assertIsNone(page)

    def test_admin_shuoshuo(self):
        """管理说说"""
        test_shuo = Shuoshuo.query.filter_by(shuo='This a test shuoshuo.').first()
        test_shuo.shuo = 'This a new shuoshuo.'
        db.session.add(test_shuo)
        db.session.commit()
        shuo = Shuoshuo.query.filter_by(shuo='This a new shuoshuo.').first()
        self.assertIsNotNone(shuo)

    def test_delete_shuoshuo(self):
        """删除说说"""
        test_shuo = Shuoshuo.query.filter_by(shuo='This a new shuoshuo.').first()
        db.session.delete(test_shuo)
        db.session.commit()
        shuo = Shuoshuo.query.filter_by(shuo='This a new shuoshuo.').first()
        self.assertIsNone(shuo)

    def test_admin_link(self):
        """管理链接"""
        test_social_link = SiteLink.query.filter_by(isFriendLink=False).first()
        test_friend_link = SiteLink.query.filter_by(isFriendLink=True).first()
        test_social_link.name = 'google'
        test_friend_link.name ='kyu'
        db.session.add(test_social_link)
        db.session.add(test_friend_link)
        db.session.commit()
        social_link = SiteLink.query.filter_by(isFriendLink=False).first()
        friend_link = SiteLink.query.filter_by(isFriendLink=True).first()
        self.assertEqual(social_link.name, 'google')
        self.assertNotEqual(friend_link.name, 'yukun')

    def test_delete_link(self):
        """删除链接"""
        test_social_link = SiteLink.query.filter_by(name='google').first()
        test_friend_link = SiteLink.query.filter_by(name='kyu').first()
        db.session.delete(test_social_link)
        db.session.delete(test_friend_link)
        db.session.commit()
        social_link = SiteLink.query.filter_by(name='google').first()
        friend_link = SiteLink.query.filter_by(name='kyu').first()
        self.assertIsNone(social_link)
        self.assertIsNone(friend_link)

    def test_admin_article(self):
        """管理专栏文章"""
        test_article = Article.query.filter_by(title='test-article').first()
        test_article.title = 'test'
        db.session.add(test_article)
        db.session.commit()
        article = Article.query.filter_by(title='test').first()
        self.assertIsNotNone(article)

    def test_delete_article(self):
        """删除专栏文章"""
        test_article = Article.query.filter_by(title='test').first()
        db.session.delete(test_article)
        db.session.commit()
        article = Article.query.filter_by(title='test').first()
        self.assertIsNone(article)

    def test_admin_column(self):
        """管理专栏"""
        test_column = Column.query.filter_by(column='test').first()
        test_column.column = 'test_admin'
        db.session.add(test_column)
        db.session.commit()
        column = Column.query.filter_by(column='test_admin').first()
        self.assertIsNotNone(column)

    def test_delete_column(self):
        """删除专栏"""
        test_column = Column.query.filter_by(column='test_admin').first()
        db.session.delete(test_column)
        db.session.commit()
        column = Column.query.filter_by(column='test_admin').first()
        self.assertIsNone(column)

    def test_admin_plugin(self):
        """管理插件"""
        test_box = SideBox.query.filter_by(title='test-box').first()
        test_box.title = 'test'
        db.session.add(test_box)
        db.session.commit()
        box = SideBox.query.filter_by(title='test').first()
        self.assertIsNotNone(box)

    def test_delete_plugin(self):
        """删除插件"""
        test_box = SideBox.query.filter_by(title='test').first()
        db.session.delete(test_box)
        db.session.commit()
        box = SideBox.query.filter_by(title='test').first()
        self.assertIsNone(box)


if __name__ == '__main__':
    # unittest.main()
    def suite():
        tests = ['test_init', 'test_add_admin', 'test_tourists_login', 'test_admin_login', 'test_add_article',
                'test_add_page', 'test_add_shuoshuo', 'test_add_link',
                'test_add_column', 'test_add_column_article', 'test_add_plugin',
                'test_admin_post', 'test_delete_post', 'test_admin_page',
                'test_delete_page', 'test_admin_shuoshuo', 'test_delete_shuoshuo',
                'test_admin_link', 'test_delete_link', 'test_admin_article',
                'test_delete_article', 'test_admin_column','test_delete_column',
                'test_admin_plugin', 'test_delete_plugin', 'test_end']

        return unittest.TestSuite(map(AdminTestCase, tests))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
