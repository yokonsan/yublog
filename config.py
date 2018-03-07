import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    CSRF_ENABLED = True
    SECRET_KEY = 'you-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    POSTS_PER_PAGE = 10
    ADMIN_POSTS_PER_PAGE = 20
    ACHIVES_POSTS_PER_PAGE = 20
    SEARCH_POSTS_PER_PAGE = 15
    COMMENTS_PER_PAGE = 10
    ADMIN_COMMENTS_PER_PAGE = 50

    UPLOAD_PATH = './app/static/upload/'

    # 博客信息
    # 管理员姓名
    ADMIN_NAME = '俞坤'
    # 管理员登录信息
    ADMIN_LOGIN_NAME = 'yukun'
    # 登录密码
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'password'
    # 博客名
    SITE_NAME = '意外'
    # 博客标题
    SITE_TITLE = '俞坤的博客'
    # 管理员简介
    ADMIN_PROFILE = '克制力，执行力'

    # RSS站点信息
    # 站点协议
    WEB_PROTOCOL = 'http'
    # 站点域名
    WEB_URL = 'www.yukunweb.com'
    # 站点创建时间
    WEB_START_TIME = '2017-05-25'
    # 显示条数
    RSS_COUNTS = 10

    # 发送邮件用户登录
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    # 客户端登录密码非正常登录密码
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_SERVER = os.getenv('MAIL_SERVER') or 'smtp.qq.com'
    MAIL_PORT = os.getenv('MAIL_PORT') or '465'

    ADMIN_MAIL_SUBJECT_PREFIX = 'blog'
    ADMIN_MAIL_SENDER = 'admin 944682328@qq.com'
    # 接收邮件通知的邮箱
    ADMIN_MAIL = os.getenv('ADMIN_MAIL')
    # 搜索最小字节
    WHOOSHEE_MIN_STRING_LEN = 1

    # cache 使用 Redis 数据库缓存配置
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = '127.0.0.1'
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = os.getenv('CACHE_REDIS_DB') or ''
    CHCHE_REDIS_PASSWORD = os.getenv('CHCHE_REDIS_PASSWORD') or ''

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost:3306/mydb'
    DEBUG = True

class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@localhost:3306/mydb'
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # 把错误发给管理
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.ADMIN_MAIL_SENDER,
            toaddrs=[cls.ADMIN_MAIL],
            subject=cls.ADMIN_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

class UnixConfig(ProductionConfig):

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.INFO)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
