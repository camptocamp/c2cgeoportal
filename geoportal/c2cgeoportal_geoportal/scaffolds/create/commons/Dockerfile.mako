FROM camptocamp/geomapfish-build:${geomapfish_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY . /opt/${package}_commons

RUN pip install --disable-pip-version-check --no-cache-dir --no-deps --editable=/opt/${package}_commons
