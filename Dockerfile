FROM python:3.8-bullseye
MAINTAINER Nick Bolten <nbolten@gmail.com>

RUN apt-get update && \
    apt-get install -y \
      fiona \
      libsqlite3-mod-spatialite

RUN mkdir -p /unweaver
COPY . /unweaver

RUN pip install -r /unweaver/requirements.txt
RUN pip install /unweaver

ENTRYPOINT ["unweaver"]
