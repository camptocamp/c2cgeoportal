#############################################################################################################
# The base image with apt and python packages.

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.7.3 AS base
LABEL maintainer Camptocamp "info@camptocamp.com"

# Fail on error on pipe, see: https://github.com/hadolint/hadolint/wiki/DL4006.
# Treat unset variables as an error when substituting.
# Print commands and their arguments as they are executed.
SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

ENV \
    DEBIAN_FRONTEND=noninteractive \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    SETUPTOOLS_USE_DISTUTILS=stdlib

# hadolint ignore=SC1091,DL3008
RUN \
    . /etc/os-release && \
    apt-get update && \
    apt-get upgrade --assume-yes && \
    apt-get install --assume-yes --no-install-recommends apt-utils && \
    apt-get install --assume-yes --no-install-recommends apt-transport-https gettext less gnupg libpq5 \
         python3-pip python3-dev python3-wheel python3-pkgconfig libgraphviz-dev libpq-dev binutils gcc g++ cython3 && \
    echo "For Chrome installed by Pupetter" && \
    apt-get install --assume-yes --no-install-recommends libx11-6 libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxi6 libxtst6 libnss3 libcups2 libxss1 libxrandr2 libasound2 libatk1.0-0 \
    libatk-bridge2.0-0 libpangocairo-1.0-0 libgtk-3.0 libxcb-dri3-0 libgbm1 libxshmfence1 && \
    echo "deb https://deb.nodesource.com/node_16.x ${VERSION_CODENAME} main" > /etc/apt/sources.list.d/nodesource.list && \
    curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
    apt-get update && \
    apt-get install --assume-yes --no-install-recommends 'nodejs=16.*' && \
    apt-get clean && \
    rm --recursive --force /var/lib/apt/lists/* && \
    ln -s /usr/local/lib/libproj.so.* /usr/local/lib/libproj.so && \
    ln -s /usr/bin/cython3 /usr/bin/cython

COPY requirements.txt /tmp/
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt && \
    rm --recursive --force /tmp/*

COPY Pipfile Pipfile.lock /tmp/
# hadolint disable=DL3003
RUN cd /tmp && PIP_NO_BINARY=fiona,rasterio,shapely PROJ_DIR=/usr/local/ pipenv sync --system --clear && \
    rm --recursive --force /usr/local/lib/python3.*/dist-packages/tests/ /tmp/* /root/.cache/* && \
    strip /usr/local/lib/python3.*/dist-packages/*/*.so && \
    apt-get auto-remove --assume-yes binutils gcc g++

ENV NODE_PATH=/usr/lib/node_modules
ENV TEST=false


#############################################################################################################
# Finally used for all misk task, will not be used on prod runtime

FROM base AS tools

# Fail on error on pipe, see: https://github.com/hadolint/hadolint/wiki/DL4006.
# Treat unset variables as an error when substituting.
# Print commands and their arguments as they are executed.
SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

CMD ["tail", "--follow", "--zero-terminated", "/dev/null"]

# hadolint ignore=SC1091,DL3008
RUN \
    . /etc/os-release && \
    echo deb https://apt.postgresql.org/pub/repos/apt/ "${VERSION_CODENAME}-pgdg" main > \
    /etc/apt/sources.list.d/pgdg.list && \
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get install --assume-yes --no-install-recommends git make python3-dev python3-venv \
    postgresql-client net-tools iputils-ping vim vim-editorconfig vim-addon-manager tree groff-base \
    libxml2-utils bash-completion pwgen redis-tools libmagic1 dnsutils && \
    apt-get clean && \
    rm --recursive --force /var/lib/apt/lists/* && \
    curl https://raw.githubusercontent.com/awslabs/git-secrets/1.3.0/git-secrets > /usr/bin/git-secrets && \
    vim-addon-manager --system-wide install editorconfig && \
    echo 'set hlsearch  " Highlight search' > /etc/vim/vimrc.local && \
    echo 'set wildmode=list:longest  " Completion menu' >> /etc/vim/vimrc.local && \
    echo 'set term=xterm-256color " Make home and end working' >> /etc/vim/vimrc.local

COPY Pipfile Pipfile.lock /tmp/
# hadolint ignore=DL3003
RUN \
    cd /tmp && \
    pipenv sync --system --clear --dev && \
    rm --recursive --force /tmp/* /root/.cache/*

ENV PATH=/root/.local/bin/:${PATH}

WORKDIR /opt/c2cgeoportal
COPY ci/applications*.yaml ./
RUN \
  python3 -m venv venv && \
  venv/bin/pip install c2cciutils==1.4.13 && \
  venv/bin/c2cciutils-download-applications --applications-file=applications.yaml --versions-file=applications-versions.yaml && \
  rm -rf venv

COPY bin/npm-packages /usr/bin/
COPY geoportal/package.json /opt/c2cgeoportal/geoportal/
WORKDIR /opt/c2cgeoportal/geoportal

# hadolint ignore=SC2046,DL3016
RUN \
    npm-packages --src=package.json --dst=/tmp/npm-packages && \
    npm --no-optional --global --unsafe-perm --no-package-lock install $(cat /tmp/npm-packages) && \
    npm cache clear --force && \
    rm -rf /tmp/* && \
    npm-packages \
    @types @typescript-eslint @storybook ol-cesium jasmine-core karma karma-chrome-launcher \
    karma-jasmine karma-sinon karma-sourcemap-loader karma-webpack \
    react react-dom cypress chromatic jscodeshift sass start-server-and-test \
    typedoc typescript \
    --src=/usr/lib/node_modules/ngeo/package.json --src=package.json --dst=npm-packages

# Workaround to fix the chokidar error
RUN ln -s /usr/lib/node_modules/webpack-dev-server/node_modules/chokidar /usr/lib/node_modules/

COPY admin/package.json /opt/c2cgeoportal/admin/
WORKDIR /opt/c2cgeoportal/admin
RUN \
    npm --no-optional --no-package-lock install && \
    npm cache clear --force && \
    rm -rf /tmp/*

# hadolint ignore=SC2046,DL3016
RUN \
    npm install --no-optional --global --unsafe-perm --no-package-lock $(cat /opt/c2cgeoportal/geoportal/npm-packages) && \
    npm cache clear --force && \
    rm -rf /tmp/* && \
    git clone --branch=v1.7.x --depth=1 --single-branch https://github.com/angular/angular.js.git \
    /tmp/angular && \
    mv /tmp/angular/src/ngLocale/ /opt/angular-locale/ && \
    rm -rf /tmp/angular && \
    curl --output /opt/jasperreport.xsd https://jasperreports.sourceforge.net/xsd/jasperreport.xsd

WORKDIR /opt/c2cgeoportal
COPY dependencies.mk vars.yaml ./
COPY .tx/ .tx/
ARG MAJOR_VERSION
ENV MAJOR_VERSION=$MAJOR_VERSION
RUN make --makefile=dependencies.mk dependencies

COPY bin/ /usr/bin/
COPY scripts/ scripts/
COPY geoportal/c2cgeoportal_geoportal/scaffolds/ geoportal/c2cgeoportal_geoportal/scaffolds/
COPY build.mk lingua.cfg ./

RUN make --makefile=build.mk build && \
    mkdir -p 'geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_create_template/geoportal/interfaces/' && \
    import-ngeo-apps --html --canvas desktop_alt /usr/lib/node_modules/ngeo/contribs/gmf/apps/desktop_alt/index.html.ejs \
    'geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_create_template/geoportal/interfaces/desktop_alt.html.mako' && \
    mkdir -p 'geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_create_template/geoportal/{{cookiecutter.package}}_geoportal/static/images/' && \
    cp /usr/lib/node_modules/ngeo/contribs/gmf/apps/desktop/image/background-layer-button.png \
    'geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_create_template/geoportal/{{cookiecutter.package}}_geoportal/static/images/'

COPY commons/ commons/
COPY geoportal/ geoportal/
COPY admin/ admin/
ARG VERSION
ENV VERSION=$VERSION

RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=commons \
    --editable=geoportal \
    --editable=admin

RUN make --makefile=build.mk \
    geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
    admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot

# For awscli
RUN echo 'complete -C aws_completer aws' >> /etc/bash_completion.d/aws_completer && \
    mv /usr/bin/bashrc ~/.bashrc && \
    git config --global --add safe.directory /src
COPY scripts/clone_schema.sql /opt/

WORKDIR /src

ARG MAJOR_MINOR_VERSION
ENV MAJOR_MINOR_VERSION=$MAJOR_MINOR_VERSION

RUN pip freeze > /requirements.txt


#############################################################################################################
# Cleaned image used to copy files to the runner

FROM tools AS tools-cleaned

# Removes unwanted and unsecured (see bandit checks) files
RUN rm --recursive --force -- geoportal/c2cgeoportal_geoportal/scaffolds \
    */tests \
    commons/c2cgeoportal_commons/testing/ \
    geoportal/c2cgeoportal_geoportal/scripts/c2cupgrade.py


#############################################################################################################
# Image used to run the project

FROM base AS runner

RUN apt-get remove --yes --auto-remove gcc

ARG MAJOR_VERSION
ENV MAJOR_VERSION=$MAJOR_VERSION
ARG VERSION
ENV VERSION=$VERSION

COPY bin/npm-packages /usr/bin/

WORKDIR /opt/c2cgeoportal/geoportal
COPY geoportal/package.json ./

ENV PUPPETEER_CACHE_DIR=/opt
# hadolint ignore=SC2046,DL3016
RUN npm --no-optional --unsafe-perm --no-package-lock install && \
    npm cache clear --force && \
    rm -rf /tmp/*

COPY package.json /tmp/

# hadolint ignore=SC2046,DL3016
RUN cd /tmp && \
    npm-packages --src=package.json --dst=npm-packages && \
    npm --no-optional --global --unsafe-perm --no-package-lock install $(cat npm-packages) && \
    npm cache clear --force && \
    rm -rf /tmp/*

COPY bin/eval-templates bin/wait-db bin/list4vrt bin/azure /usr/bin/
COPY --from=tools-cleaned /opt/c2cgeoportal /opt/c2cgeoportal
COPY --from=tools-cleaned /usr/lib/node_modules/ngeo/buildtools/check-example.js /usr/bin/

WORKDIR /opt/c2cgeoportal
RUN \
    ln -s /opt/c2cgeoportal/commons/c2cgeoportal_commons/alembic /opt && \
    python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=commons \
    --editable=geoportal \
    --editable=admin && \
    python3 -m compileall -q /opt/c2cgeoportal /usr/local/lib/python3.* \
    -x '(/usr/local/lib/python3.*/dist-packages/(pipenv|networkx)/|/opt/c2cgeoportal/geoportal/c2cgeoportal_geoportal/scaffolds/)'

WORKDIR /opt/c2cgeoportal/geoportal

RUN adduser www-data root \
    && pip freeze > /requirements.txt
# From c2cwsgiutils


ENV TERM=linux \
  LANG=C.UTF-8 \
  PKG_CONFIG_ALLOW_SYSTEM_LIBS=OHYESPLEASE

ENV C2C_BASE_PATH=/c2c \
  C2C_REDIS_TIMEOUT=3 \
  C2C_REDIS_SERVICENAME=mymaster \
  C2C_BROADCAST_PREFIX=broadcast_api_ \
  C2C_SQL_PROFILER_ENABLED=0 \
  C2C_DEBUG_VIEW_ENABLED=0 \
  C2C_ENABLE_EXCEPTION_HANDLING=0

# End from c2cwsgiutils

ENV C2CGEOPORTAL_THEME_TIMEOUT=300


#############################################################################################################
# Image that run the checks

FROM tools AS checks

WORKDIR /opt/c2cgeoportal

# For mypy
RUN \
    touch /usr/local/lib/python3.10/dist-packages/zope/__init__.py && \
    touch /usr/local/lib/python3.10/dist-packages/c2c/__init__.py

COPY setup.cfg .prospector.yaml .pylintrc .bandit.yaml checks.mk ./
COPY .git ./.git/
COPY scripts/pylint-copyright.py ./scripts/

RUN make --makefile=checks.mk checks
