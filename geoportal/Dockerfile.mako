FROM camptocamp/geomapfish-commons:${major_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

ARG GIT_TAG
ARG MAJOR_VERSION

COPY npm-packages /opt/c2cgeoportal_geoportal/npm-packages

RUN \
  npm install --no-optional --global `cat /opt/c2cgeoportal_geoportal/npm-packages` && \
  chmod go+r -R /usr/lib/node_modules/@camptocamp/closure-util/.deps/compiler/* && \
  rm --recursive --force ~/.npm /usr/lib/node_modules/openlayers/node_modules/

RUN \
  svg2ttf /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.svg \
    /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.ttf && \
  ttf2eot /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.ttf \
    /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.eot && \
  ttf2woff /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.ttf \
    /usr/lib/node_modules/ngeo/contribs/gmf/fonts/gmf-icons.woff && \
  convert /usr/lib/node_modules/ngeo/contribs/gmf/cursors/grabbing.png \
    /usr/lib/node_modules/ngeo/contribs/gmf/cursors/grab.cur && \
  convert /usr/lib/node_modules/ngeo/contribs/gmf/cursors/grabbing.png \
    /usr/lib/node_modules/ngeo/contribs/gmf/cursors/grab.cur && \
  for f in `ls -1 /usr/lib/node_modules/ngeo/contribs/gmf/less/`; \
    do sed --in-place --expression='s/..\/..\/..\/node_modules\//\/usr\/lib\/node_modules\//g' \
      /usr/lib/node_modules/ngeo/contribs/gmf/less/$f; \
  done


RUN \
  mkdir --parents /opt/googleclosurecompiler-externs && \
  curl --max-redirs 0 --location --output /opt/googleclosurecompiler-externs/angular-1.6.js https://raw.githubusercontent.com/google/closure-compiler/master/contrib/externs/angular-1.6.js && \
  curl --max-redirs 0 --location --output /opt/googleclosurecompiler-externs/angular-1.6-q_templated.js https://raw.githubusercontent.com/google/closure-compiler/master/contrib/externs/angular-1.6-q_templated.js && \
  curl --max-redirs 0 --location --output /opt/googleclosurecompiler-externs/angular-1.6-http-promise_templated.js https://raw.githubusercontent.com/google/closure-compiler/master/contrib/externs/angular-1.6-http-promise_templated.js && \
  curl --max-redirs 0 --location --output /opt/googleclosurecompiler-externs/jquery-1.9.js https://raw.githubusercontent.com/google/closure-compiler/master/contrib/externs/jquery-1.9.js && \
  mkdir --parents /opt/angular-locale && \
  for LANG in en fr de it en-ch fr-ch de-ch it-ch; \
  do \
    wget -O /opt/angular-locale/angular-locale_$LANG.js https://raw.githubusercontent.com/angular/angular.js/`grep ^angular.js= /usr/lib/node_modules/ngeo/github_versions | cut --delimiter = --fields 2 | tr --delete '\r\n'`/src/ngLocale/angular-locale_$LANG.js; \
  done

COPY . /opt/c2cgeoportal_geoportal

RUN chmod go+r -R /opt/c2cgeoportal_geoportal && \
  pip install --disable-pip-version-check --no-cache-dir --no-deps --editable=/opt/c2cgeoportal_geoportal

ENV NODE_PATH=/usr/lib/node_modules \
    LOG_LEVEL=INFO \
    GUNICORN_ACCESS_LOG_LEVEL=INFO \
    C2CGEOPORTAL_LOG_LEVEL=WARN \
    VISIBLE_WEB_HOST=example.com \
    VISIBLE_WEB_PROTOCOL=https \
    VISIBLE_ENTRY_POINT=/ \
    PGHOST=db \
    PGHOST_SLAVE=db \
    PGPORT=5432 \
    PGUSER=www-data \
    PGPASSWORD=www-data \
    PGDATABASE=geomapfish \
    PGSCHEMA=main \
    PGSCHEMA_STATIC=main_static \
    TINYOWS_URL=http://tinyows/ \
    MAPSERVER_URL=http://mapserver/ \
    PRINT_URL=http://print:8080/print/
