ARG VERSION

FROM camptocamp/c2cwsgiutils:3-lite AS c2cwsgiutils

FROM camptocamp/qgis-server:${VERSION} AS base
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY --from=c2cwsgiutils /opt/c2cwsgiutils /opt/c2cwsgiutils
COPY --from=c2cwsgiutils /usr/local/lib/python3.7/dist-packages/c2cwsgiutils.egg-link \
    /usr/local/lib/python3.6/dist-packages/c2cwsgiutils.egg-link
RUN echo /opt/c2cwsgiutils >> /usr/local/lib/python3.6/dist-packages/easy-install.pth

COPY requirements.txt /tmp/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt

#############################################################################################################

FROM debian:stretch AS lint

RUN apt-get update
RUN apt-get install --assume-yes --no-install-recommends apt-utils
RUN apt-get install --assume-yes --no-install-recommends python3-pip python3-setuptools
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir wheel

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
COPY --from=camptocamp/geomapfish /opt/c2cgeoportal/commons /opt/c2cgeoportal/commons

RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=/opt/c2cgeoportal/commons

#############################################################################################################

FROM runner as tests

COPY --from=camptocamp/geomapfish-tools /opt/c2cgeoportal/commons/c2cgeoportal_commons/testing \
    /opt/c2cgeoportal/commons/c2cgeoportal_commons/testing
COPY tests/requirements.txt /tmp/

RUN python3 -m pip install --requirement=/tmp/requirements.txt

COPY tests/geomapfish.yaml /etc/qgisserver/geomapfish.yaml
COPY tests/multiple_ogc_server.yaml /etc/qgisserver/multiple_ogc_server.yaml
COPY tests/functional /src/tests/functional

ENV PYTHONPATH /var/www/plugins:/usr/local/share/qgis/python/:/opt

RUN mkdir -p /pytest && chmod 777 /pytest
WORKDIR /pytest
