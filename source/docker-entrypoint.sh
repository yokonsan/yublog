#!/bin/bash

echo "db init"

if [ ! -d "/migrations/" ];then
  echo "migrations already exists"
else
  python manage.py db init
fi

echo "db migrate"

python manage.py db migrate -m "v1.0"

echo "db upgrade"

python manage.py db upgrade

echo "db add admin"

python manage.py add_admin

echo "uwsgi start"

nohup uwsgi config.ini > app.log 2>&1 &
