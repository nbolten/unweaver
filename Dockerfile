FROM python:3.6-stretch
MAINTAINER Nick Bolten <nbolten@gmail.com>

RUN apt-get update && \
    apt-get install -y \
      fiona \
      libsqlite3-mod-spatialite

# RUN pip3 install --upgrade pip

RUN pip install poetry

RUN mkdir -p /install
WORKDIR /install

COPY ./unweaver /install/unweaver
COPY ./pyproject.toml /install/pyproject.toml
COPY ./poetry.lock /install/poetry.lock

RUN poetry install

CMD ["poetry", "run", "unweaver"]
