#!/bin/sh

DATABASE_FILE=./persist/db.sqlite3

if [ ! -f "$DATABASE_FILE" ]; then
    sudo --user=pclink --preserve-env python manage.py makemigrations
    sudo --user=pclink --preserve-env python manage.py migrate
    sudo --user=pclink --preserve-env python manage.py createsuperuser --noinput
fi

if [ "$MIGRATE" = "1" ]; then
    sudo --user=pclink --preserve-env python manage.py makemigrations
    sudo --user=pclink --preserve-env python manage.py migrate
fi

echo "Running rabbitmq..."
rabbitmq-server -detached

echo "Collecting static files..."
sudo --user=pclink --preserve-env python manage.py collectstatic --clear --noinput

echo "Starting celery..."
sudo --user=pclink --preserve-env celery -A pc_link_rest worker --detach

echo "Starting uWSGI..."
sudo --user=pclink --preserve-env uwsgi --ini django.ini
