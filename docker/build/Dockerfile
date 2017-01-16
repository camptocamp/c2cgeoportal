FROM debian:jessie
MAINTAINER Stéphane Brunner <stephane.brunner@camptocamp.com>

COPY run /usr/bin/
COPY . /tmp/

RUN \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends vim tree make git curl ca-certificates apt-transport-https python libpq5 libgeos-c1 gettext python-dev libpq-dev libgeos-dev libjpeg-dev gcc && \
  curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
  echo 'deb https://deb.nodesource.com/node_4.x jessie main' > /etc/apt/sources.list.d/nodesource.list && \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends nodejs && \
  cd /tmp && \
  curl https://bootstrap.pypa.io/get-pip.py > get-pip.py && \
  python get-pip.py `cat base-requirements.txt` && \
  pip install --requirement dev-requirements.txt && \
  apt-get purge --assume-yes --auto-remove curl python-dev libpq-dev libgeos-dev libjpeg-dev gcc apt-transport-https && \
  apt-get clean && \
  rm --recursive --force /tmp/* /var/tmp/* i/var/lib/apt/lists/* /root/.cache/*

WORKDIR /src

ENV PYTHONPATH /build/venv/lib/python2.7/site-packages/

ENTRYPOINT ["run"]
