import logging
from os import getenv


class Config(object):
    CSRF_ENABLED = True
    SECRET_KEY = "yublog-guess"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

    POSTS_PER_PAGE = 10
    ADMIN_POSTS_PER_PAGE = 20
    ARCHIVES_POSTS_PER_PAGE = 20
    SEARCH_POSTS_PER_PAGE = 15
    COMMENTS_PER_PAGE = 10
    ADMIN_COMMENTS_PER_PAGE = 50

    UPLOAD_PATH = "./yublog/static/upload/"
    # 图片路径
    IMAGE_UPLOAD_PATH = "./yublog/static/upload/image/"

    # 数据库配置
    MYSQL_HOST = getenv("MYSQL_HOST") or "127.0.0.1"
    MYSQL_DATABASE = getenv("MYSQL_DATABASE") or "yublog"
    MYSQL_PASSWORD = getenv("MYSQL_PASSWORD") or "password"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/{MYSQL_DATABASE}"

    # 博客信息
    # 管理员姓名
    ADMIN_NAME = "yublog"
    # 管理员登录信息
    ADMIN_LOGIN_NAME = "yublog"
    # 登录密码
    ADMIN_PASSWORD = getenv("ADMIN_PASSWORD") or "password"
    # 博客名
    SITE_NAME = "yublog"
    # 博客标题
    SITE_TITLE = "银时的博客"
    # 管理员简介
    ADMIN_PROFILE = "克制力，执行力"

    # RSS站点信息
    # 站点协议
    WEB_PROTOCOL = "http"
    # 站点域名
    WEB_URL = "www.domain.com"
    # 站点创建时间
    WEB_START_TIME = "2017-05-25"
    # 显示条数
    RSS_COUNTS = 10

    # 发送邮件用户登录
    MAIL_USERNAME = getenv("MAIL_USERNAME")
    # 客户端登录密码非正常登录密码
    MAIL_PASSWORD = getenv("MAIL_PASSWORD")
    MAIL_SERVER = getenv("MAIL_SERVER") or "smtp.qq.com"
    MAIL_PORT = getenv("MAIL_PORT") or "465"

    ADMIN_MAIL_SUBJECT_PREFIX = "yublog"
    ADMIN_MAIL_SENDER = "admin email"
    # 接收邮件通知的邮箱
    ADMIN_MAIL = getenv("ADMIN_MAIL")
    # 搜索最小字节
    WHOOSHEE_MIN_STRING_LEN = 1

    # cache 使用 Redis 数据库缓存配置
    CACHE_TYPE = "redis"
    CACHE_KEY_PREFIX = "yublog"
    CACHE_REDIS_HOST = getenv("CACHE_REDIS_HOST") or "127.0.0.1"
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = getenv("CACHE_REDIS_DB") or 0
    CHCHE_REDIS_PASSWORD = getenv("CHCHE_REDIS_PASSWORD") or ""

    # 七牛云存储配置
    NEED_PIC_BED = False
    QN_ACCESS_KEY = getenv("QN_ACCESS_KEY") or ""
    QN_SECRET_KEY = getenv("QN_SECRET_KEY") or ""
    # 七牛空间名
    QN_PIC_BUCKET = "bucket-name"
    # 七牛外链域名
    QN_PIC_DOMAIN = "domain-url"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    @classmethod
    def init_app(cls, app):
        from loguru import logger

        class InterceptHandler(logging.Handler):
            def emit(self, record):
                logger_opt = logger.opt(depth=6, exception=record.exc_info)
                logger_opt.log(record.levelno, record.getMessage())

        Config.init_app(app)
        app.logger.addHandler(InterceptHandler())
        logging.basicConfig(handlers=[InterceptHandler()], level="INFO")


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # 把错误发给管理
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, "MAIL_USERNAME", None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, "MAIL_USE_TLS", None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.ADMIN_MAIL_SENDER,
            toaddrs=[cls.ADMIN_MAIL],
            subject=cls.ADMIN_MAIL_SUBJECT_PREFIX + " Application Error",
            credentials=credentials,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class DockerConfig(ProductionConfig):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "docker": DockerConfig,
    "default": DevelopmentConfig
}
