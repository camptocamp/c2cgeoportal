FROM camptocamp/geomapfish_build_dev
MAINTAINER Stéphane Brunner <stephane.brunner@camptocamp.com>

COPY . /tmp/

RUN \
  cd /tmp && \
  pip install . && \
  rm -rf /tmp/*

WORKDIR /src

ENV PYTHONPATH /build/venv/lib/python2.7/site-packages/
