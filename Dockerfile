FROM python:3-alpine

RUN apk add --no-cache --virtual build-dependecies alpine-sdk build-base linux-headers
RUN apk add --no-cache pcre-dev mariadb-connector-c-dev

RUN pip install --no-cache-dir uwsgi

RUN mkdir -p /home/ubuntu/static /home/ubuntu/media

COPY requirements.txt /pclink/
RUN pip install --no-cache-dir -r /pclink/requirements.txt

RUN apk del build-dependecies

WORKDIR /pclink/
COPY . /pclink/
ARG DJANGO_SECRET_KEY
RUN python manage.py collectstatic
RUN rm -r /pclink/*