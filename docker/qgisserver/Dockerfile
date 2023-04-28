ARG VERSION

FROM camptocamp/c2cwsgiutils:release_3-lite AS c2cwsgiutils

FROM camptocamp/qgis-server:${VERSION} AS base
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY --from=c2cwsgiutils /opt/c2cwsgiutils /opt/c2cwsgiutils
COPY --from=c2cwsgiutils /usr/local/lib/python3.7/dist-packages/c2cwsgiutils.egg-link \
    /usr/local/lib/python3.6/dist-packages/c2cwsgiutils.egg-link
RUN echo /opt/c2cwsgiutils >> /usr/local/lib/python3.6/dist-packages/easy-install.pth
COPY requirements.txt /tmp/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt

COPY Pipfile Pipfile.lock /tmp/
RUN cd /tmp && PIP_NO_BINARY=:all: pipenv install --system --deploy --clear

#############################################################################################################

FROM debian:buster AS lint

RUN apt-get update
RUN apt-get install --assume-yes --no-install-recommends apt-utils
RUN apt-get install --assume-yes --no-install-recommends python3-pip python3-setuptools
COPY requirements.txt /tmp/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt

COPY Pipfile Pipfile.lock /tmp/
RUN cd /tmp && LC_ALL=C.UTF-8 LANG=C.UTF-8 pipenv install --system --deploy --clear --dev

COPY . /src/
RUN flake8 /src
RUN pylint --errors-only --disable=import-error /src/geomapfish_qgisserver
RUN cd /src && \
    isort --check-only --diff --settings-path=`pwd` --recursive .
RUN bandit --recursive -ll /src

#############################################################################################################

FROM base AS runner

COPY geomapfish_qgisserver/* /var/www/plugins/geomapfish_qgisserver/
COPY logging.ini /var/www/
COPY --from=camptocamp/geomapfish /opt/c2cgeoportal/commons /opt/c2cgeoportal/commons

RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=/opt/c2cgeoportal/commons

ENV LOG_LEVEL=INFO \
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

RUN cd /tmp && pipenv install --system --clear
RUN python3 -m pip install pytest-timeout

COPY tests/geomapfish.yaml /etc/qgisserver/geomapfish.yaml
COPY tests/multiple_ogc_server.yaml /etc/qgisserver/multiple_ogc_server.yaml
COPY tests/functional /src/tests/functional

ENV PYTHONPATH /var/www/plugins:/usr/local/share/qgis/python/:/opt

RUN mkdir -p /pytest && chmod 777 /pytest
WORKDIR /pytest
