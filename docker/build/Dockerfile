FROM camptocamp/c2cwsgiutils:2
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN \
  . /etc/os-release && \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends tree apt-transport-https gettext sudo && \
  echo "deb https://deb.nodesource.com/node_6.x ${VERSION_CODENAME} main" > /etc/apt/sources.list.d/nodesource.list && \
  curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
# Docker source list should be like it but actually it's empty...
# echo "deb [arch=amd64] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list && \
  echo "deb [arch=amd64] https://download.docker.com/linux/debian stretch stable" > /etc/apt/sources.list.d/docker.list && \
  curl --silent https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends 'nodejs=6.*' docker-ce openjdk-8-jre-headless && \
  apt-get clean && \
  rm --recursive --force /var/lib/apt/lists/*

COPY requirements.txt /tmp/

RUN \
  cd /tmp && \
  pip install --disable-pip-version-check --no-cache-dir --requirement requirements.txt && \
  # for mypy
  touch /usr/local/lib/python3.6/dist-packages/zope/__init__.py && \
  touch /usr/local/lib/python3.6/dist-packages/c2c/__init__.py && \
  rm --recursive --force /tmp/* /var/tmp/* /root/.cache/*

COPY sudoers /etc/
COPY bin/* /usr/bin/

WORKDIR /src

ENTRYPOINT ["run"]
