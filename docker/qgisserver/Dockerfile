ARG VERSION

FROM camptocamp/qgis-server:${VERSION} AS base
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY requirements.txt /tmp/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt

COPY python/ /tmp/python/


RUN apt-get update && \
    apt-get upgrade --assume-yes && \
    apt-get install --assume-yes --no-install-recommends libpython3-dev libpq-dev gcc cython3 && \
    apt-get clean && \
    rm --recursive --force /var/lib/apt/lists/* && \
    ln -s /usr/bin/cython3 /usr/bin/cython && \
    cd /tmp/python/$(python3 --version|awk '{print $2}'|awk -F '.' '{print $1 "." $2}') && \
    PIP_NO_BINARY=shapely pipenv sync --system --clear --verbose && \
    python -c 'import yaml' && \
    rm -rf /root/.local/share/virtualenv /root/.local/share/virtualenvs && \
    rm -rf /usr/bin/cython && \
    apt-get remove --assume-yes libpython3-dev libpq-dev gcc cython3

#############################################################################################################

FROM ubuntu:20.04 AS lint

RUN apt update
RUN apt install --assume-yes --no-install-recommends python3-pip python3-dev libpython3-dev libpq-dev gcc
COPY requirements.txt /tmp/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt

COPY python/ /tmp/python/
RUN cd /tmp/python/$(python3 --version|awk '{print $2}'|awk -F '.' '{print $1 "." $2}') && \
    LC_ALL=C.UTF-8 LANG=C.UTF-8 pipenv sync --system --clear --dev

COPY . /src/
RUN cd /src && prospector

#############################################################################################################

FROM base AS runner

COPY geomapfish_qgisserver/* /var/www/plugins/geomapfish_qgisserver/
COPY logging.ini /var/www/
COPY --from=camptocamp/geomapfish /opt/c2cgeoportal/commons /opt/c2cgeoportal/commons

RUN VERSION=0.0.0 python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=/opt/c2cgeoportal/commons \
    && pip freeze > /requirements.txt

ENV LOG_LEVEL=INFO \
    LOG_TYPE=console \
    C2CGEOPORTAL_LOG_LEVEL=INFO \
    C2CWSGIUTILS_LOG_LEVEL=INFO \
    SQL_LOG_LEVEL=WARN \
    OTHER_LOG_LEVEL=WARN \
    QGIS_SERVER_LOG_LEVEL=2 \
    CPL_VSIL_CURL_USE_CACHE=TRUE \
    CPL_VSIL_CURL_CACHE_SIZE=128000000 \
    CPL_VSIL_CURL_USE_HEAD=FALSE \
    GDAL_DISABLE_READDIR_ON_OPEN=TRUE

#############################################################################################################

FROM runner as tests

COPY --from=camptocamp/geomapfish-tools /opt/c2cgeoportal/commons/c2cgeoportal_commons/testing \
    /opt/c2cgeoportal/commons/c2cgeoportal_commons/testing
# Workaround to make the build working on GitHub Action
# See also: https://github.com/moby/moby/issues/37965
RUN true
COPY tests/Pipfile tests/Pipfile.lock /tmp/

RUN cd /tmp && pipenv sync --system --clear
RUN python3 -m pip install pytest-timeout

COPY tests/geomapfish.yaml /etc/qgisserver/geomapfish.yaml
COPY tests/multiple_ogc_server.yaml /etc/qgisserver/multiple_ogc_server.yaml
COPY tests/functional /src/tests/functional

ENV PYTHONPATH /var/www/plugins:/usr/local/share/qgis/python/:/opt

RUN mkdir -p /pytest && chmod 777 /pytest
WORKDIR /pytest
