FROM python:3.5
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends vim tree make git curl ca-certificates apt-transport-https libpq5 libgeos-c1 gettext libpq-dev libgeos-dev libjpeg-dev gcc default-jre-headless && \
  curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
  echo 'deb https://deb.nodesource.com/node_6.x jessie main' > /etc/apt/sources.list.d/nodesource.list && \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends nodejs && \
  apt-get clean && \
  rm --recursive --force /var/lib/apt/lists/*

COPY dev-requirements.txt fixversions.txt /tmp/

RUN \
  cd /tmp && \
  pip install --disable-pip-version-check --no-cache-dir --requirement dev-requirements.txt && \
  rm --recursive --force /tmp/* /var/tmp/* /root/.cache/*

COPY run /usr/bin/

WORKDIR /src

ENV PYTHONPATH /build/venv/lib/python3.5/site-packages/

ENTRYPOINT ["run"]
