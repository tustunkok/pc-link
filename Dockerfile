FROM python:3

RUN pip install uwsgi

RUN mkdir -p /home/ubuntu/static /home/ubuntu/media
RUN chown www-data:www-data /home/ubuntu/media

COPY requirements.txt /pclink/
RUN pip install -r /pclink/requirements.txt

WORKDIR /pclink/
COPY . /pclink/
RUN python manage.py collectstatic

CMD ["uwsgi", "--ini", "/pclink/django.ini"]
