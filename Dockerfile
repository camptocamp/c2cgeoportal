FROM camptocamp/geomapfish-build-dev:latest
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN \
  npm install --global \
    angular@1.6.5 \
    angular-animate@1.6.5 \
    angular-dynamic-locale@0.1.32 \
    angular-float-thead@0.1.2 \
    angular-gettext@2.3.10 \
    angular-gettext-tools@2.3.6 \
    angular-sanitize@1.6.5 \
    angular-touch@1.6.5 \
    angular-ui-date@1.1.1 \
    angular-ui-slider@0.4.0 \
    async@2.5.0 \
    bootstrap@3.3.7 \
    clean-css@4.0.1 \
    clean-css-cli@4.1.6 \
    closure-util@git://github.com/camptocamp/closure-util#487fac6 \
    console-control-strings@1.1.0 \
    corejs-typeahead@1.1.1 \
    d3@4.10.0 \
    eslint@4.4.0 \
    eslint-config-openlayers@7.0.0 \
    file-saver@1.3.3 \
    floatthead@2.0.3 \
    font-awesome@4.7.0 \
    fs-extra@4.0.1 \
    jasmine-core@2.7.0 \
    jquery@3.2.1 \
    jsts@1.4.0 \
    less@2.7.2 \
    less-plugin-autoprefix@1.5.1 \
    less-plugin-clean-css@1.5.1 \
    moment@2.18.1 \
    ngeo@git://github.com/camptocamp/ngeo#master \
    nomnom@1.8.1 \
    openlayers@4.3.1 \
    phantomjs-prebuilt@2.1.14 \
    proj4@2.4.4 \
    svg2ttf@4.1.0 \
    temp@0.8.3 \
    ttf2eot@2.0.0 \
    ttf2woff@2.0.1 \
    typeahead.js@0.11.1 \
    walk@2.3.9 && \
  chmod go+r -R /usr/lib/node_modules/closure-util/.deps/compiler/* && \
  rm --recursive --force ~/.npm

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

COPY . /opt/c2cgeoportal

RUN chmod go+r -R /opt/c2cgeoportal && \
  pip install --disable-pip-version-check --no-cache-dir --no-deps --editable /opt/c2cgeoportal

WORKDIR /src
