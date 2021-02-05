FROM python:3.8-buster

ARG PC_USER="pclink"
ARG PC_UID="1000"
ARG PC_GID="1000"

EXPOSE 8000

USER root

COPY . /pc_link_rest/

RUN chmod a+x /pc_link_rest/start.sh && mkdir /pc_link_rest/persist/
RUN pip install --no-cache-dir -r /pc_link_rest/requirements.txt

RUN groupadd -g $PC_GID $PC_USER && \
    useradd -M -u $PC_UID -g $PC_GID -s /sbin/nologin $PC_USER && \
    chown -R $PC_USER:$PC_USER /pc_link_rest/

WORKDIR /pc_link_rest/

USER $PC_USER
CMD /bin/sh start.sh