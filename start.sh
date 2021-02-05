#!/bin/sh

DATABASE_FILE=./persist/db.sqlite3
STATIC_DIR=./static/

if [ ! -f "$DATABASE_FILE" ]; then
    python manage.py makemigrations
    python manage.py migrate
    python manage.py createsuperuser --noinput
fi

if [ ! -d "$STATIC_DIR"  ]; then
    python manage.py collectstatic
fi

uwsgi --ini django.ini
