FROM python:3-alpine

RUN apk add --update alpine-sdk build-base linux-headers pcre-dev

RUN pip install uwsgi

RUN mkdir -p /home/ubuntu/static /home/ubuntu/media

RUN apk add --update mariadb-connector-c-dev

COPY requirements.txt /pclink/
RUN pip install -r /pclink/requirements.txt

RUN apk del alpine-sdk build-base linux-headers

WORKDIR /pclink/
COPY . /pclink/
RUN python manage.py collectstatic
