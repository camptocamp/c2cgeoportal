#############################################################################################################
# The base image with apt and python packages.

FROM camptocamp/c2cwsgiutils:3 AS base
LABEL maintainer Camptocamp "info@camptocamp.com"

ENV \
  DEBIAN_FRONTEND=noninteractive \
  SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

RUN \
  . /etc/os-release && \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends apt-utils && \
  apt-get install --assume-yes --no-install-recommends apt-transport-https gettext less && \
  echo "For Chome installed by Pupetter" && \
  apt-get install --assume-yes --no-install-recommends libx11-6 libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxi6 libxtst6 libnss3 libcups2 libxss1 libxrandr2 libasound2 libatk1.0-0 \
    libatk-bridge2.0-0 libpangocairo-1.0-0 libgtk-3.0 && \
  echo "deb https://deb.nodesource.com/node_10.x ${VERSION_CODENAME} main" > /etc/apt/sources.list.d/nodesource.list && \
  curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends 'nodejs=10.*' && \
  apt-get clean && \
  rm --recursive --force /var/lib/apt/lists/*

COPY requirements.txt /tmp/
RUN \
  python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt && \
  rm --recursive --force /tmp/* /var/tmp/* /root/.cache/*


#############################################################################################################
# Finally used for all misk task, will not be used on prod runtime

FROM base AS tools

CMD ["sleep", "infinity"]
RUN \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends git make postgresql-client gdal-bin net-tools iputils-ping \
        vim vim-editorconfig vim-addon-manager tree groff-base libxml2-utils bash-completion && \
  apt-get clean && \
  rm --recursive --force /var/lib/apt/lists/* && \
  curl https://raw.githubusercontent.com/awslabs/git-secrets/1.3.0/git-secrets > /usr/bin/git-secrets && \
  vim-addon-manager --system-wide install editorconfig && \
  echo 'set hlsearch  " Highlight search' > /etc/vim/vimrc.local && \
  echo 'set wildmode=list:longest  " Completion menu' >> /etc/vim/vimrc.local && \
  echo 'set term=xterm-256color " Make home and end working' >> /etc/vim/vimrc.local

COPY requirements-dev.txt /tmp/
RUN \
  python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements-dev.txt && \
  rm --recursive --force /tmp/* /var/tmp/* /root/.cache/*

COPY bin/npm-packages /usr/bin/
COPY geoportal/package.json /opt/c2cgeoportal/geoportal/
WORKDIR /opt/c2cgeoportal/geoportal
RUN \
  npm-packages --src=package.json --dst=/tmp/npm-packages && \
  npm --no-optional --global --unsafe-perm --no-package-lock install `cat /tmp/npm-packages` && \
  npm cache clear --force && \
  rm -rf /tmp/*

RUN npm-packages \
  @camptocamp/cesium @types @typescript-eslint jasmine-core karma karma-chrome-launcher \
  karma-jasmine karma-sinon karma-sourcemap-loader karma-webpack \
  typedoc \
  --src=/usr/lib/node_modules/ngeo/package.json --src=package.json --dst=npm-packages

COPY admin/package.json /opt/c2cgeoportal/admin/
WORKDIR /opt/c2cgeoportal/admin
RUN \
  npm --no-optional --no-package-lock install && \
  npm cache clear --force && \
  rm -rf /tmp/*

RUN \
  npm install --no-optional --global --unsafe-perm --no-package-lock $(cat /opt/c2cgeoportal/geoportal/npm-packages) && \
  npm cache clear --force && \
  rm -rf /tmp/*
RUN \
  git clone --branch=v1.7.x --depth=1 --single-branch https://github.com/angular/angular.js.git \
  /tmp/angular && \
  mv /tmp/angular/src/ngLocale/ /opt/angular-locale/ &&\
  rm -rf /tmp/angular
RUN \
  curl --output /opt/jasperreport.xsd http://jasperreports.sourceforge.net/xsd/jasperreport.xsd

COPY . /opt/c2cgeoportal/
WORKDIR /opt/c2cgeoportal/
RUN mv bin/import-ngeo-apps bin/eval-templates bin/wait-db bin/transifex-init bin/run bin/run-git /usr/bin/
ARG MAJOR_VERSION
ENV MAJOR_VERSION=$MAJOR_VERSION
RUN make --makefile=internal.mk build

ARG VERSION
ENV VERSION=$VERSION
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=/opt/c2cgeoportal/commons \
    --editable=/opt/c2cgeoportal/geoportal \
    --editable=/opt/c2cgeoportal/admin

# For awscli
RUN echo 'complete -C aws_completer aws' >> /etc/bash_completion.d/aws_completer
COPY bin/bashrc ~/.bashrc
COPY scripts/clone_schema.sql /opt/

ENV NODE_PATH=/usr/lib/node_modules

WORKDIR /src


#############################################################################################################
# Cleaned image used to copy files to the runner

FROM tools AS tools-cleaned

# Removes unwanted and unsecured (see bandit checks) files
RUN rm --recursive --force /opt/c2cgeoportal/geoportal/c2cgeoportal_geoportal/scaffolds \
    /opt/c2cgeoportal/*/tests \
    /opt/c2cgeoportal/commons/c2cgeoportal_commons/testing/ \
    /opt/c2cgeoportal/geoportal/c2cgeoportal_geoportal/scripts/c2cupgrade.py


#############################################################################################################
# Image used to run the project

FROM base AS runner

COPY bin/npm-packages /usr/bin/
COPY package.json /tmp/
RUN \
  cd /tmp && \
  npm-packages --src=package.json --dst=npm-packages && \
  npm --no-optional --global --unsafe-perm --no-package-lock install $(cat npm-packages) && \
  npm cache clear --force && \
  rm -rf /tmp/*

COPY bin/eval-templates bin/wait-db bin/update-po bin/list4vrt /usr/bin/
COPY --from=tools-cleaned /opt/c2cgeoportal /opt/c2cgeoportal
COPY --from=tools-cleaned /usr/lib/node_modules/ngeo/buildtools/check-example.js /usr/bin/

WORKDIR /opt/c2cgeoportal/geoportal

RUN \
  ln -s /opt/c2cgeoportal/commons/c2cgeoportal_commons/alembic /opt && \
  python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=/opt/c2cgeoportal/commons \
    --editable=/opt/c2cgeoportal/geoportal \
    --editable=/opt/c2cgeoportal/admin && \
    python3 -m compileall -q /opt/c2cgeoportal /usr/local/lib/python3.7 \
        -x /usr/local/lib/python3.7/dist-packages/dateutils/

RUN adduser www-data root


#############################################################################################################
# Image that run the checks

FROM tools AS checks
WORKDIR /opt/c2cgeoportal

# For mypy
RUN \
  touch /usr/local/lib/python3.7/dist-packages/zope/__init__.py && \
  touch /usr/local/lib/python3.7/dist-packages/c2c/__init__.py

RUN make --makefile=internal.mk checks
