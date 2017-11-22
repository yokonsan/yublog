import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    CSRF_ENABLED = True
    SECRET_KEY = 'you-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    POSTS_PER_PAGE = 10
    ADMIN_POSTS_PER_PAGE = 20

    # 博客信息
    # 管理员姓名
    ADMIN_NAME = '俞坤'
    # 管理员登录信息
    ADMIN_LOGIN_NAME = 'yukun'
    # 登录密码
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'password'
    # 博客名
    SITE_NAME = '意外'
    # 管理员简介
    ADMIN_PROFILE = '克制力，执行力'


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost:3306/blog'
    DEBUG = True

class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
