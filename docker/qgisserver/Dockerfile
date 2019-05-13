ARG VERSION
FROM camptocamp/qgis-server:${VERSION} AS base
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY requirements.txt /tmp/
RUN python3 -m pip install --requirement=/tmp/requirements.txt

#############################################################################################################

FROM debian:stretch AS lint

RUN apt-get update
RUN apt-get install --assume-yes --no-install-recommends apt-utils
RUN apt-get install --assume-yes --no-install-recommends python3-pip python3-setuptools
RUN python3 -m pip install wheel

COPY requirements-dev.txt /src/
RUN python3 -m pip install --requirement=/src/requirements-dev.txt

COPY . /src/
RUN flake8 /src
RUN pylint --errors-only --disable=import-error /src/geomapfish_qgisserver
# TODO: add --disallow-untyped-defs
RUN	mypy --ignore-missing-imports --strict-optional --follow-imports skip /src/geomapfish_qgisserver

#############################################################################################################

FROM base AS runner

COPY geomapfish_qgisserver/* /var/www/plugins/geomapfish_qgisserver/
COPY --from=camptocamp/geomapfish /opt/c2cgeoportal_commons/* /opt/c2cgeoportal_commons/

RUN python3 -m pip install --editable=/opt/c2cgeoportal_commons

#############################################################################################################

FROM runner as tests

COPY tests/requirements.txt /tmp/

RUN python3 -m pip install --requirement=/tmp/requirements.txt

COPY tests/geomapfish.yaml /etc/qgisserver/geomapfish.yaml
COPY tests/multiple_ogc_server.yaml /etc/qgisserver/multiple_ogc_server.yaml
COPY tests/functional /src/tests/functional

ENV PYTHONPATH /var/www/plugins:/usr/local/share/qgis/python/:/opt

RUN mkdir -p /pytest && chmod 777 /pytest
WORKDIR /pytest
