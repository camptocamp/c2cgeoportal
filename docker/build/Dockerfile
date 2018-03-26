FROM camptocamp/c2cwsgiutils:1.7
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends tree apt-transport-https gettext sudo && \
  echo 'deb https://deb.nodesource.com/node_6.x jessie main' > /etc/apt/sources.list.d/nodesource.list && \
  curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
  echo "deb http://apt.dockerproject.org/repo debian-jessie main" > /etc/apt/sources.list.d/docker.list && \
  curl --silent http://apt.dockerproject.org/gpg | apt-key add - && \
  echo "deb http://http.debian.net/debian jessie-backports main" > /etc/apt/sources.list.d/backport.list && \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends nodejs docker-engine && \
  apt-get install --assume-yes --no-install-recommends --target-release=jessie-backports openjdk-8-jre-headless && \
  apt-get clean && \
  rm --recursive --force /var/lib/apt/lists/*

COPY requirements.txt /tmp/

RUN \
  cd /tmp && \
  pip install --disable-pip-version-check --no-cache-dir --requirement requirements.txt && \
  # for mypy
  touch /usr/local/lib/python3.6/site-packages/zope/__init__.py && \
  touch /usr/local/lib/python3.6/site-packages/c2c/__init__.py && \
  rm --recursive --force /tmp/* /var/tmp/* /root/.cache/*

COPY run /usr/bin/
COPY sudoers /etc/
COPY bin/* /usr/bin/

WORKDIR /src

ENV PYTHONPATH /build/venv/lib/python3.6/site-packages/

ENTRYPOINT ["run"]
