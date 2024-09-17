FROM ghcr.io/osgeo/gdal:ubuntu-small-3.7.3 AS base-all
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
  apt-get update && \
  apt-get upgrade --assume-yes && \
  apt-get install --assume-yes --no-install-recommends gettext-base python3-pip python3-dev gcc g++ && \
  apt-get clean && \
  rm --recursive --force /var/lib/apt/lists/*

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
RUN poetry export --output=requirements.txt

# Base, the biggest thing is to install the Python packages
FROM base-all as runner

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    python3 -m pip install --disable-pip-version-check --no-deps --requirement=/poetry/requirements.txt \
    && (strip /usr/local/lib/python3.*/dist-packages/*/*.so || true) \
    && pip freeze > /requirements.txt

ARG VERSION
ENV VERSION=$VERSION

COPY bin/ /usr/bin/
COPY haproxy/ /etc/haproxy/
COPY haproxy_dev/ /etc/haproxy_dev/

ENTRYPOINT [ "/usr/bin/entrypoint" ]
