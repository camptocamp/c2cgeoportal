FROM camptocamp/geomapfish-build-dev:${major_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY . /opt/c2cgeoportal_commons

ARG GIT_TAG
ARG MAJOR_VERSION
ENV TRAVIS_TAG=$TRAVIS_TAG MAJOR_VERSION=$MAJOR_VERSION

RUN chmod go+r -R /opt/c2cgeoportal_commons && \
  mv /opt/c2cgeoportal_commons/c2cgeoportal_commons/alembic /opt && \
  pip install --disable-pip-version-check --no-cache-dir --no-deps --editable=/opt/c2cgeoportal_commons
