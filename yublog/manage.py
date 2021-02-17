#!/usr/bin/env python
import os

# if os.path.exists('../.env'):
#     for line in open('../.env', encoding='utf-8'):
#         if line .find('#') > -1:
#             line = line.split('#')[0]
#         var = line.strip().split('=')
#         if len(var) == 2:
#             os.environ[var[0]] = var[1]

from .app import create_app, db
from .app.models import Admin, Post, Tag, Category, SiteLink, \
    Page, LoveMe, Comment, Shuoshuo, SideBox
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Admin=Admin, Post=Post, Tag=Tag,
                Category=Category, SiteLink=SiteLink, Page=Page,
                LoveMe=LoveMe, Comment=Comment, Shuoshuo=Shuoshuo, SideBox=SideBox)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def clear_alembic():
    from yublog.app.models import Alembic
    Alembic.clear()


@manager.command
def add_admin():
    from yublog.app.models import Admin, LoveMe
    from yublog.config import Config
    # 创建管理员
    admin = Admin(site_name=Config.SITE_NAME, site_title=Config.SITE_TITLE, name=Config.ADMIN_NAME,
                  profile=Config.ADMIN_PROFILE, login_name=Config.ADMIN_LOGIN_NAME,
                  password=Config.ADMIN_PASSWORD)
    # 创建love-me
    love = LoveMe(loveMe=666)
    # 创建留言板
    guest_book = Page(title='留言板', url_name='guest-book', canComment=True,
                      isNav=False, body='留言板')
    db.session.add(admin)
    db.session.add(love)
    db.session.add(guest_book)
    db.session.commit()


if __name__ == '__main__':
    manager.run()
