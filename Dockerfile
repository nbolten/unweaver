FROM python:3.8-bullseye
MAINTAINER Nick Bolten <nbolten@gmail.com>

RUN apt-get update && \
    apt-get install -y \
      fiona \
      libsqlite3-mod-spatialite

RUN mkdir -p /unweaver
WORKDIR /unweaver
COPY ./unweaver /unweaver/unweaver
COPY ./pyproject.toml /unweaver/pyproject.toml
COPY ./poetry.lock /unweaver/poetry.lock

RUN pip install /unweaver

ENTRYPOINT ["unweaver"]
