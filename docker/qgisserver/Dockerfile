ARG VERSION=latest
FROM camptocamp/qgis-server:${VERSION}
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY requirements.txt /tmp/
RUN \
    . /etc/os-release \
    && apt-get update \
    && apt-get dist-upgrade --assume-yes --no-install-recommends \
    && apt-get install --assume-yes --no-install-recommends gcc g++ \
    && apt-get clean \
    && rm --recursive --force /var/lib/apt/lists/* \
    && python3 -m pip install --requirement /tmp/requirements.txt \
    && apt-get remove --purge --autoremove --yes gcc g++

COPY geomapfish_qgisserver/* /var/www/plugins/geomapfish_qgisserver/
COPY commons /opt/c2cgeoportal_commons

RUN python3 -m pip install --editable /opt/c2cgeoportal_commons
