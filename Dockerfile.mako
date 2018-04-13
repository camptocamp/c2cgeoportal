FROM camptocamp/geomapfish-build-dev:${major_version}
LABEL maintainer Camptocamp "info@camptocamp.com"

ARG VERSION
ENV VERSION=$VERSION

COPY npm-packages /opt/npm-packages

RUN \
  npm install --no-optional --global `cat /opt/npm-packages` && \
  npm cache clear && \
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
