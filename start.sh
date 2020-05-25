#!/bin/sh

sleep 40
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --noinput
uwsgi --ini /pclink/django.ini