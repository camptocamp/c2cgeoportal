FROM debian:stretch
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends gettext-base python3-pip python3-setuptools && \
  apt-get clean && \
  rm --recursive --force /var/lib/apt/lists/*

COPY requirements.txt /tmp
RUN python3 -m pip install --requirement=/tmp/requirements.txt
