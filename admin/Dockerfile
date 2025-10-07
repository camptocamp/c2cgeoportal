# Used for development: please do not remove this file

# hadolint ignore=DL3007
FROM camptocamp/geomapfish-tools:latest

COPY . /app
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --editable=.

ENTRYPOINT []
CMD ["pserve", "--reload", "c2c://development.ini"]
