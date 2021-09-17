#!/bin/sh

git log --full-history --date-order --pretty=format:"[%ad - %an - %h]  %s" --date=format:"%d/%m/%Y" > git-commit-history.log
docker build --rm -t pclink:latest .
docker save pclink:latest | bzip2 > /tmp/pclink_latest.tar.bz2
scp /tmp/pclink_latest.tar.bz2 tustunkok@pc-link.atilim.edu.tr:/home/tustunkok/docker-images/
