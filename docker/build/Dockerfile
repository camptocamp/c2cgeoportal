FROM camptocamp/c2cwsgiutils:2
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN \
    . /etc/os-release \
    && echo deb http://apt.postgresql.org/pub/repos/apt/ ${VERSION_CODENAME}-pgdg main > /etc/apt/sources.list.d/pgdg.list \
    && curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update \
    && apt-get dist-upgrade --assume-yes --no-install-recommends \
    && apt-get install --assume-yes --no-install-recommends tree apt-transport-https gettext libxml2-utils postgresql-client \
    && echo "deb https://deb.nodesource.com/node_10.x ${VERSION_CODENAME} main" > /etc/apt/sources.list.d/nodesource.list \
    && curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - \
    &&
    # Docker source list should be like it but actually it's empty...
    # echo "deb [arch=amd64] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list && \
    echo "deb [arch=amd64] https://download.docker.com/linux/debian stretch stable" > /etc/apt/sources.list.d/docker.list \
    && curl --silent https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
    && apt-get update \
    && apt-get install --assume-yes --no-install-recommends 'nodejs=10.*' docker-ce openjdk-8-jre-headless \
    && apt-get clean \
    && rm --recursive --force /var/lib/apt/lists/*

COPY requirements.txt /tmp/

RUN \
    cd /tmp \
    && pip install --disable-pip-version-check --no-cache-dir --requirement requirements.txt \
    &&
    # for mypy
    touch /usr/local/lib/python3.6/dist-packages/zope/__init__.py \
    && touch /usr/local/lib/python3.6/dist-packages/c2c/__init__.py \
    && rm --recursive --force /tmp/* /var/tmp/* /root/.cache/*

COPY bin/* /usr/bin/
COPY etc/bash_completion.d/* /etc/bash_completion.d/

WORKDIR /src

ENTRYPOINT ["run"]
