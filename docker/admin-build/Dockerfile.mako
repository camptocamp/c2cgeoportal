FROM camptocamp/geomapfish-commons:${major_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY npm-packages /tmp/npm-packages

RUN npm install --no-optional --global `cat /tmp/npm-packages`
