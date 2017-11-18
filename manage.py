#!/usr/bin/env python
import os
from app import create_app, db
from app.models import Admin, Post, Tag, Category, SocialLink, Page
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Admin=Admin, Post=Post, Tag=Tag, \
            Category=Category, SocialLink=SocialLink, Page=Page)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()