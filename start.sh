#!/bin/sh

DATABASE_FILE=./persist/db.sqlite3

if [ ! -f "$DATABASE_FILE" ]; then
    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser --noinput
fi

python manage.py collectstatic --clear --noinput
uwsgi --ini django.ini
