#!/usr/bin/env python
import os
from app import create_app, db
from app.models import Admin, Post, Tag, Category, SocialLink, Page
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

if os.path.exists('.env'):
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

def make_shell_context():
    return dict(app=app, db=db, Admin=Admin, Post=Post, Tag=Tag, \
            Category=Category, SocialLink=SocialLink, Page=Page)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def clearAlembic():
    from app.models import Alembic
    Alembic.clear_A()

@manager.command
def addAdmin():
    from app.models import Admin
    from config import Config
    admin = Admin(site_name=Config.SITE_NAME, site_title=Config.SITE_TITLE ,name=Config.ADMIN_NAME, \
                  profile=Config.ADMIN_PROFILE, login_name=Config.ADMIN_LOGIN_NAME, \
                  password=Config.ADMIN_PASSWORD)
    db.session.add(admin)
    db.session.commit()


if __name__ == '__main__':
    manager.run()