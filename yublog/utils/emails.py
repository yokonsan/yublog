import smtplib
from email.header import Header
from email.mime.text import MIMEText

from flask import current_app

from yublog.utils.as_sync import sync_request_context


def send_mail(to_addr, msg):
    @sync_request_context
    def _send():
        mail_username = current_app.config['MAIL_USERNAME']
        mail_password = current_app.config['MAIL_PASSWORD']
        mail_server = current_app.config['MAIL_SERVER']
        mail_port = current_app.config['MAIL_PORT']
        if not (mail_username and mail_password):
            current_app.logger.warning('无邮箱配置，邮件发送失败。')
            return

        content = MIMEText(msg, 'html', 'utf-8')
        content['Subject'] = Header('新的评论', 'utf-8').encode()
        server = smtplib.SMTP_SSL(mail_server, mail_port)
        server.login(mail_username, mail_password)
        server.sendmail(mail_username, [to_addr], content.as_string())
        server.quit()

    return _send()
