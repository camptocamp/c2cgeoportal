FROM camptocamp/geomapfish-build-dev:2.3
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY . /opt/c2cgeoportal_commons

RUN chmod go+r -R /opt/c2cgeoportal_commons && \
  pip install --disable-pip-version-check --no-cache-dir --no-deps --editable=/opt/c2cgeoportal_commons
