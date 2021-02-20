# coding: utf-8

from flask import current_app


class ToolsSettings(object):
    # 获取配置信息
    ADMIN_NAME = current_app.config['ADMIN_NAME']
    SITE_NAME = current_app.config['SITE_NAME']
    SITE_TITLE = current_app.config['SITE_TITLE']
    WEB_PROTOCOL = current_app.config['WEB_PROTOCOL']
    WEB_URL = current_app.config['WEB_URL']
    WEB_START_TIME = current_app.config['WEB_START_TIME']
    RSS_COUNTS = current_app.config['RSS_COUNTS']

    # 邮件配置
    MAIL_USERNAME = current_app.config['MAIL_USERNAME']
    MAIL_PASSWORD = current_app.config['MAIL_PASSWORD']
    MAIL_SERVER = current_app.config['MAIL_SERVER']
    MAIL_PORT = current_app.config['MAIL_PORT']


tools_settings = ToolsSettings()
