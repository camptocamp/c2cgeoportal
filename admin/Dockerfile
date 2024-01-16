# Used for development: please do not remove this file

# hadolint ignore=DL3007
FROM camptocamp/geomapfish:latest

COPY requirements-dev.txt /tmp/
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=/tmp/requirements-dev.txt

COPY . /app
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --no-deps --editable=/app

ENTRYPOINT []
CMD ["pserve", "--reload", "c2c://development.ini"]
