#!/bin/sh

echo "Waiting database to be ready..."
python manage.py wait_for_database

echo "Applying migrations..."
python manage.py migrate

if [ "$CREATE_SUPER_USER" = "1" ]; then
    python manage.py createsuperuser --noinput
fi

echo "Collecting static files..."
python manage.py collectstatic --clear --noinput

echo "Starting Celery..."
celery -A pc_link_rest worker --detach

echo "Starting Gunicorn..."
gunicorn -b pclink:8000 -w 2 --forwarded-allow-ips="nginx" pc_link_rest.wsgi
