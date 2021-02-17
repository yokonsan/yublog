# coding: utf-8

from yublog.config import Config
config = Config()


class ToolsSettings(object):
    # 获取配置信息
    ADMIN_NAME = config.ADMIN_NAME
    SITE_NAME = config.SITE_NAME
    SITE_TITLE = config.SITE_TITLE
    WEB_PROTOCOL = config.WEB_PROTOCOL
    WEB_URL = config.WEB_URL
    WEB_START_TIME = config.WEB_START_TIME
    RSS_COUNTS = config.RSS_COUNTS

    # 邮件配置
    MAIL_USERNAME = config.MAIL_USERNAME
    MAIL_PASSWORD = config.MAIL_PASSWORD
    MAIL_SERVER = config.MAIL_SERVER
    MAIL_PORT = config.MAIL_PORT


tools_settings = ToolsSettings()
