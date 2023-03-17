# Used for development: please do not remove this file

FROM camptocamp/geomapfish:latest
MAINTAINER Camptocamp "info@camptocamp.com"

COPY requirements-dev.txt /tmp/
RUN \
    python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements-dev.txt \
    && rm --recursive --force /tmp/* /var/tmp/* /root/.cache/*

COPY . /app
WORKDIR /app

RUN \
    python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=/app

ENTRYPOINT []
CMD pserve --reload c2c://development.ini
