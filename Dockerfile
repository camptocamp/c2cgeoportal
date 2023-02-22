#############################################################################################################
# The base image with apt and python packages.

FROM camptocamp/c2cwsgiutils:release_3-lite AS base
LABEL maintainer Camptocamp "info@camptocamp.com"

ENV \
    DEBIAN_FRONTEND=noninteractive \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    SETUPTOOLS_USE_DISTUTILS=stdlib

RUN \
    . /etc/os-release && \
    apt-get update && \
    apt-get dist-upgrade --assume-yes --no-install-recommends && \
    apt-get install --assume-yes --no-install-recommends apt-utils && \
    apt-get install --assume-yes --no-install-recommends apt-transport-https gettext less && \
    echo "For Chrome installed by Pupetter" && \
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
RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --requirement=/tmp/requirements.txt && \
    rm --recursive --force /tmp/*

COPY Pipfile Pipfile.lock /tmp/
RUN cd /tmp && pipenv install --system --clear && \
    rm --recursive --force /usr/local/lib/python3.7/dist-packages/tests/ /tmp/* /root/.cache/*

ENV NODE_PATH=/usr/lib/node_modules
ENV TEST=false


#############################################################################################################
# Finally used for all misk task, will not be used on prod runtime

FROM base AS tools

CMD ["sleep", "infinity"]
RUN \
    . /etc/os-release && \
    echo deb http://apt.postgresql.org/pub/repos/apt/ ${VERSION_CODENAME}-pgdg main > \
    /etc/apt/sources.list.d/pgdg.list && \
    curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get install --assume-yes --no-install-recommends git make python3.7-dev gcc postgresql-client gdal-bin \
    net-tools iputils-ping vim vim-editorconfig vim-addon-manager tree groff-base libxml2-utils \
    bash-completion pwgen && \
    apt-get clean && \
    rm --recursive --force /var/lib/apt/lists/* && \
    curl https://raw.githubusercontent.com/awslabs/git-secrets/1.3.0/git-secrets > /usr/bin/git-secrets && \
    vim-addon-manager --system-wide install editorconfig && \
    echo 'set hlsearch  " Highlight search' > /etc/vim/vimrc.local && \
    echo 'set wildmode=list:longest  " Completion menu' >> /etc/vim/vimrc.local && \
    echo 'set term=xterm-256color " Make home and end working' >> /etc/vim/vimrc.local

COPY Pipfile Pipfile.lock /tmp/
RUN \
    cd /tmp && \
    pipenv install --system --clear --dev && \
    rm --recursive --force /tmp/* /root/.cache/*

COPY bin/npm-packages bin/update-po /usr/bin/
COPY geoportal/package.json /opt/c2cgeoportal/geoportal/
WORKDIR /opt/c2cgeoportal/geoportal
RUN \
    npm-packages --src=package.json --dst=/tmp/npm-packages && \
    npm --no-optional --global --unsafe-perm --no-package-lock install `cat /tmp/npm-packages` && \
    npm cache clear --force && \
    rm -rf /tmp/*

RUN npm-packages \
    @types @typescript-eslint ol-cesium jasmine-core karma karma-chrome-launcher \
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

WORKDIR /opt/c2cgeoportal

ARG MAJOR_VERSION
ENV MAJOR_VERSION=$MAJOR_VERSION

COPY bin/ bin/
COPY scripts/ scripts/
COPY geoportal/c2cgeoportal_geoportal/scaffolds/ geoportal/c2cgeoportal_geoportal/scaffolds/
COPY build.mk lingua.cfg ./

RUN mv bin/import-ngeo-apps bin/eval-templates bin/wait-db bin/transifex-init bin/run bin/run-git /usr/bin/
RUN make --makefile=build.mk build

COPY commons/ commons/
COPY geoportal/ geoportal/
COPY admin/ admin/
RUN make --makefile=build.mk \
    geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
    admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot

ARG VERSION=2.5
ENV VERSION=$VERSION

RUN python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=commons \
    --editable=geoportal \
    --editable=admin

# For awscli
RUN echo 'complete -C aws_completer aws' >> /etc/bash_completion.d/aws_completer && \
    git config --global --add safe.directory /src
COPY bin/bashrc ~/.bashrc
COPY scripts/clone_schema.sql /opt/

WORKDIR /src


#############################################################################################################
# Cleaned image used to copy files to the runner

FROM tools AS tools-cleaned

# Removes unwanted and unsecured (see bandit checks) files
RUN rm --recursive --force geoportal/c2cgeoportal_geoportal/scaffolds \
    */tests \
    commons/c2cgeoportal_commons/testing/ \
    geoportal/c2cgeoportal_geoportal/scripts/c2cupgrade.py


#############################################################################################################
# Image used to run the project

FROM base AS runner

ARG MAJOR_VERSION
ENV MAJOR_VERSION=$MAJOR_VERSION
ARG VERSION
ENV VERSION=$VERSION

COPY bin/npm-packages /usr/bin/
COPY package.json /tmp/
RUN \
    cd /tmp && \
    npm-packages --src=package.json --dst=npm-packages && \
    npm --no-optional --global --unsafe-perm --no-package-lock install $(cat npm-packages) && \
    npm cache clear --force && \
    rm -rf /tmp/*

COPY bin/eval-templates bin/wait-db bin/list4vrt /usr/bin/
COPY --from=tools-cleaned /opt/c2cgeoportal /opt/c2cgeoportal
COPY --from=tools-cleaned /usr/lib/node_modules/ngeo/buildtools/check-example.js /usr/bin/

WORKDIR /opt/c2cgeoportal
RUN \
    ln -s /opt/c2cgeoportal/commons/c2cgeoportal_commons/alembic /opt && \
    python3 -m pip install --disable-pip-version-check --no-cache-dir --no-deps \
    --editable=commons \
    --editable=geoportal \
    --editable=admin && \
    python3 -m compileall -q /opt/c2cgeoportal /usr/local/lib/python3.7 \
    -x /usr/local/lib/python3.7/dist-packages/pipenv/patched/yaml2

WORKDIR /opt/c2cgeoportal/geoportal

RUN adduser www-data root


#############################################################################################################
# Image that run the checks

FROM tools AS checks

WORKDIR /opt/c2cgeoportal

# For mypy
RUN \
    touch /usr/local/lib/python3.7/dist-packages/zope/__init__.py && \
    touch /usr/local/lib/python3.7/dist-packages/c2c/__init__.py

COPY setup.cfg .prospector.yaml .pylintrc .bandit checks.mk ./
COPY .git ./.git/
COPY scripts/pylint-copyright.py ./scripts/

RUN make --makefile=checks.mk checks
