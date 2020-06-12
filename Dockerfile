FROM python:3.7-slim
WORKDIR /pclink/
COPY . /pclink/
ARG DJANGO_SECRET_KEY

RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r /pclink/requirements.txt

RUN mkdir -p /home/ubuntu/static /home/ubuntu/media && \
    python manage.py collectstatic

RUN rm -r /pclink/* \
    apt-get purge -y \
    build-essential