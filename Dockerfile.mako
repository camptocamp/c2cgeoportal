FROM camptocamp/geomapfish-build-dev:${major_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

ARG VERSION
ENV VERSION=$VERSION

COPY npm-packages /opt/npm-packages

RUN \
  npm install --no-optional --global --unsafe-perm `cat /opt/npm-packages` && \
  npm cache clear --force

RUN \
  mkdir --parents /opt/angular-locale && \
  for LANG in en fr de it en-ch fr-ch de-ch it-ch; \
  do \
    curl --output /opt/angular-locale/angular-locale_$LANG.js https://raw.githubusercontent.com/angular/angular.js/v`grep '"angular"' /usr/lib/node_modules/ngeo/package.json | cut --delimiter \" --fields 4 | tr --delete '\r\n'`/src/ngLocale/angular-locale_$LANG.js; \
  done && \
  curl --output /opt/jasperreport.xsd http://jasperreports.sourceforge.net/xsd/jasperreport.xsd

COPY commons /opt/c2cgeoportal_commons
COPY geoportal /opt/c2cgeoportal_geoportal
COPY admin /opt/c2cgeoportal_admin

RUN \
  (cd /opt/c2cgeoportal_admin/; npm install --no-optional `cat npm-packages`) && \
  npm cache clear --force && \
  chmod go+r -R /opt/c2cgeoportal_commons /opt/c2cgeoportal_geoportal /opt/c2cgeoportal_admin && \
  ln -s /opt/c2cgeoportal_commons/c2cgeoportal_commons/alembic /opt && \
  pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=/opt/c2cgeoportal_commons \
    --editable=/opt/c2cgeoportal_geoportal \
    --editable=/opt/c2cgeoportal_admin

ENV NODE_PATH=/usr/lib/node_modules
