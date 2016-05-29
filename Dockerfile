FROM debian:jessie
MAINTAINER Stéphane Brunner <stephane.brunner@camptocamp.com>

COPY docker/run /usr/bin/
COPY . /tmp/

RUN \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends vim tree make git curl ca-certificates python libpq5 libgeos-c1 gettext python-dev libpq-dev libgeos-dev libjpeg-dev gcc && \
  cd /tmp && \
  curl https://bootstrap.pypa.io/get-pip.py > get-pip.py && \
  python get-pip.py && \
  pip install -r dev-requirements.txt && \
  pip install -r c2cgeoportal/scaffolds/update/CONST_requirements.txt && \
  apt-get purge --assume-yes --auto-remove curl python-dev libpq-dev libgeos-dev libjpeg-dev gcc && \
  apt-get clean && \
  rm -rf /tmp/* /var/tmp/* i/var/lib/apt/lists/* /root/.cache/*

WORKDIR /src

ENV PYTHONPATH /build/venv/lib/python2.7/site-packages/
