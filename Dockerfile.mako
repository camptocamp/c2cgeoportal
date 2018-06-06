FROM camptocamp/geomapfish-build-dev:${major_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

ARG VERSION
ENV VERSION=$VERSION

COPY npm-packages /opt/npm-packages

RUN \
  npm install --no-optional --global `cat /opt/npm-packages` && \
  npm cache clear

RUN \
  svg2ttf /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.svg \
    /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.ttf && \
  ttf2eot /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.ttf \
    /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.eot && \
  ttf2woff /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.ttf \
    /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.woff

RUN \
  mkdir --parents /opt/angular-locale && \
  for LANG in en fr de it en-ch fr-ch de-ch it-ch; \
  do \
    curl --output /opt/angular-locale/angular-locale_$LANG.js https://raw.githubusercontent.com/angular/angular.js/v`grep '"angular"' /usr/lib/node_modules/ngeo/package.json | cut --delimiter \" --fields 4 | tr --delete '\r\n'`/src/ngLocale/angular-locale_$LANG.js; \
  done

COPY commons /opt/c2cgeoportal_commons
COPY geoportal /opt/c2cgeoportal_geoportal
COPY admin /opt/c2cgeoportal_admin

RUN chmod go+r -R /opt/c2cgeoportal_commons /opt/c2cgeoportal_geoportal && \
  ln -s /opt/c2cgeoportal_commons/c2cgeoportal_commons/alembic /opt && \
  pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=/opt/c2cgeoportal_commons \
    --editable=/opt/c2cgeoportal_geoportal \
    --editable=/opt/c2cgeoportal_admin

ENV NODE_PATH=/usr/lib/node_modules
