#!/bin/bash

echo "db init"

if [ ! -d "migrations/" ];then
  python manage.py db init
fi

python manage.py clear_alembic

echo "db migrate"

python manage.py db migrate -m "v1.0"

echo "db upgrade"

python manage.py db upgrade

echo "db add admin"

python manage.py add_admin

echo "uwsgi start"

uwsgi config.ini
