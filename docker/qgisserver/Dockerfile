ARG VERSION

FROM camptocamp/qgis-server:${VERSION} AS base-all
LABEL maintainer Camptocamp "info@camptocamp.com"

# Fail on error on pipe, see: https://github.com/hadolint/hadolint/wiki/DL4006.
# Treat unset variables as an error when substituting.
# Print commands and their arguments as they are executed.
SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

# Used to convert the locked packages by poetry to pip requirements format
# We don't directly use `poetry install` because it force to use a virtual environment.
FROM base-all as poetry

# Install Poetry
WORKDIR /tmp
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=requirements.txt

# Do the conversion
COPY poetry.lock pyproject.toml ./
RUN poetry export --output=requirements.txt \
    && poetry export --with=dev --output=requirements-dev.txt

# Base, the biggest thing is to install the Python packages
FROM base-all as base

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    apt-get update \
    && apt-get upgrade --assume-yes \
    && apt-get install --assume-yes --no-install-recommends python3-dev libpq-dev gcc \
    && pip install --disable-pip-version-check --no-deps --requirement=/poetry/requirements.txt \
    && apt-get remove --assume-yes python3-dev libpq-dev gcc

#############################################################################################################

FROM base AS runner

COPY geomapfish_qgisserver/* /var/www/plugins/geomapfish_qgisserver/
COPY logging.ini /var/www/
# hadolint ignore=DL3022
COPY --from=camptocamp/geomapfish /opt/c2cgeoportal/commons /opt/c2cgeoportal/commons

ARG GEOMAPFISH_VERSION

RUN VERSION=$GEOMAPFISH_VERSION python3 -m pip install --disable-pip-version-check --no-deps \
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

SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

RUN --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    pip install --disable-pip-version-check --no-deps --requirement=/poetry/requirements-dev.txt

# hadolint ignore=DL3022
COPY --from=camptocamp/geomapfish /opt/c2cgeoportal/commons/c2cgeoportal_commons/testing \
    /opt/c2cgeoportal/commons/c2cgeoportal_commons/testing
ENV PYTHONPATH /var/www/plugins:/usr/local/share/qgis/python/:/opt

WORKDIR /src
RUN chmod 777 /src
COPY . ./
RUN mv tests/geomapfish.yaml /etc/qgisserver/geomapfish.yaml \
    && mv tests/multiple_ogc_server.yaml /etc/qgisserver/multiple_ogc_server.yaml

#############################################################################################################

FROM runner as final
