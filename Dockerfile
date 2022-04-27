FROM python:3.8-slim

ARG PC_USER="pclink"
ARG PC_UID="1000"
ARG PC_GID="1000"

EXPOSE 8000

USER root

RUN apt-get update && apt-get install -y \
    build-essential \
    libpcre3 \
    libpcre3-dev \
    graphviz \
    libgraphviz-dev \
    default-libmysqlclient-dev \
    nano \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

COPY . /pc_link_rest/

RUN chmod a+x /pc_link_rest/start.sh && mkdir /pc_link_rest/persist/ /pc_link_rest/static/
RUN pip install --no-cache-dir -r /pc_link_rest/requirements.txt

RUN AUTO_ADDED_PACKAGES=`apt-mark showauto` apt-get purge build-essential $AUTO_ADDED_PACKAGES -y \
    && apt-get autoremove -y

RUN groupadd -g $PC_GID $PC_USER && \
    useradd -M -u $PC_UID -g $PC_GID -s /sbin/nologin $PC_USER && \
    chown -R $PC_USER:$PC_USER /pc_link_rest/

WORKDIR /pc_link_rest/

USER $PC_USER
CMD ["./start.sh"]