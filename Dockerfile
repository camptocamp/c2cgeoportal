# Base of all section, install the apt packages
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.1 AS base-all
LABEL maintainer Camptocamp "info@camptocamp.com"

# Fail on error on pipe, see: https://github.com/hadolint/hadolint/wiki/DL4006.
# Treat unset variables as an error when substituting.
# Print commands and their arguments as they are executed.
SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update \
    && apt-get upgrade --assume-yes \
    && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes --no-install-recommends adduser git python3-pip python3-venv \
    && python3 -m venv /venv

ENV PATH=/venv/bin:$PATH

# Used to convert the locked packages by poetry to pip requirements format
# We don't directly use `poetry install` because it force to use a virtual environment.
FROM base-all AS poetry

# Install Poetry
WORKDIR /tmp
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache \
    python3 -m pip install --disable-pip-version-check --requirement=requirements.txt

# Do the conversion
COPY poetry.lock pyproject.toml ./
RUN poetry export --without-hashes --output=requirements.txt \
    && poetry export --with=dev --without-hashes --output=requirements-dev.txt

# Base, the biggest thing is to install the Python packages
FROM base-all AS base

SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    apt-get update \
    && apt-get upgrade --assume-yes \
    && apt-get install --assume-yes --no-install-recommends software-properties-common \
    && add-apt-repository ppa:savoury1/pipewire \
    && add-apt-repository ppa:savoury1/chromium \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes --no-install-recommends chromium-browser gettext gnupg libpq5 npm \
    && ln -s /usr/local/lib/libproj.so.25 /usr/local/lib/libproj.so

# shellcheck disable=SC2086
RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    apt-get update \
    && export DEV_PACKAGES="binutils gcc g++ libpq-dev python3-dev" \
    && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes --no-install-recommends \
        ${DEV_PACKAGES} \
    && PIP_NO_BINARY=fiona,rasterio GDAL_CONFIG=/usr/bin/gdal-config PROJ_DIR=/usr/local/ python3 -m pip install \
        --disable-pip-version-check --no-deps --requirement=/poetry/requirements.txt \
    && strip /venv/lib/python3.*/site-packages/*/*.so \
    && apt-get auto-remove --assume-yes binutils ${DEV_PACKAGES} \
    && python -c 'from fiona.collection import Collection'

COPY scripts/extract-messages.js /opt/c2cgeoportal/geoportal/

ENV PATH=/opt/c2cgeoportal/geoportal/node_modules/.bin:$PATH
ENV NODE_PATH=/opt/c2cgeoportal/geoportal/node_modules

#############################################################################################################
# Finally used for all misk task, will not be used on prod runtime

FROM base AS tools

SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

CMD ["tail", "--follow", "--zero-terminated", "/dev/null"]

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    . /etc/os-release \
    && echo 'deb [signed-by=/etc/apt/keyrings/postgresql.gpg] https://apt.postgresql.org/pub/repos/apt/' "${VERSION_CODENAME}-pgdg" main > /etc/apt/sources.list.d/pgdg.list \
    && curl --silent https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor --output=/etc/apt/keyrings/postgresql.gpg \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes --no-install-recommends git make g++ python3-dev \
        postgresql-client net-tools iputils-ping vim tree groff-base \
        libxml2-utils bash-completion pwgen redis-tools libmagic1 dnsutils iproute2 traceroute pkg-config \
    && curl https://raw.githubusercontent.com/awslabs/git-secrets/1.3.0/git-secrets > /usr/bin/git-secrets \
    && echo 'set hlsearch  " Highlight search' > /etc/vim/vimrc.local \
    && echo 'set wildmode=list:longest  " Completion menu' >> /etc/vim/vimrc.local \
    && echo 'set term=xterm-256color " Make home and end working' >> /etc/vim/vimrc.local

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,from=poetry,source=/tmp,target=/poetry \
    python3 -m pip install --disable-pip-version-check --no-deps --requirement=/poetry/requirements-dev.txt

WORKDIR /opt/c2cgeoportal

COPY ci/applications*.yaml .
ENV PATH=/root/.local/bin/:${PATH}
RUN c2cciutils-download-applications --applications-file=applications.yaml --versions-file=applications-versions.yaml

WORKDIR /opt/c2cgeoportal/geoportal
COPY geoportal/package.json geoportal/package-lock.json geoportal/.snyk ./

# hadolint ignore=DL3016,SC2046
RUN --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    --mount=type=cache,target=/tmp \
    npm --ignore-scripts install

COPY admin/package.json admin/package-lock.json admin/.snyk /opt/c2cgeoportal/admin/
WORKDIR /opt/c2cgeoportal/admin

# hadolint ignore=DL3016,SC2046
RUN --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    --mount=type=cache,target=/tmp \
    npm install --omit=optional --ignore-scripts \
    && rm -rf /tmp/angular \
    && git clone --branch=v1.7.x --depth=1 --single-branch https://github.com/angular/angular.js.git /tmp/angular \
    && mv /tmp/angular/src/ngLocale/ /opt/angular-locale/ \
    && curl --output /opt/jasperreport.xsd https://jasperreports.sourceforge.net/xsd/jasperreport.xsd

WORKDIR /opt/c2cgeoportal
COPY dependencies.mk vars.yaml ./
COPY .tx/ .tx/
ARG MAJOR_VERSION
ENV MAJOR_VERSION=$MAJOR_VERSION
RUN make --makefile=dependencies.mk dependencies

COPY bin/ /usr/bin/
COPY scripts/ scripts/
COPY geoportal/c2cgeoportal_geoportal/scaffolds/ geoportal/c2cgeoportal_geoportal/scaffolds/
COPY build.mk lingva.cfg ./

RUN make --makefile=build.mk build \
    && mkdir -p 'geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_create_template/geoportal/interfaces/' \
    && import-ngeo-apps --html --canvas desktop_alt geoportal/node_modules/ngeo/contribs/gmf/apps/desktop_alt/index.html.ejs \
        'geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_create_template/geoportal/interfaces/desktop_alt.html.mako' \
    && mkdir -p 'geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_create_template/geoportal/{{cookiecutter.package}}_geoportal/static/images/' \
    && cp geoportal/node_modules/ngeo/contribs/gmf/apps/desktop/image/background-layer-button.png \
        'geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/CONST_create_template/geoportal/{{cookiecutter.package}}_geoportal/static/images/'

COPY commons/ commons/
COPY geoportal/ geoportal/
COPY admin/ admin/
ARG VERSION
ENV VERSION=$VERSION

RUN --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    grep -r masterdev . || true \
    && python3 -m pip install --disable-pip-version-check --no-deps \
        --editable=commons \
        --editable=geoportal \
        --editable=admin

RUN make --makefile=build.mk \
    geoportal/c2cgeoportal_geoportal/locale/c2cgeoportal_geoportal.pot \
    admin/c2cgeoportal_admin/locale/c2cgeoportal_admin.pot \
    && git config --global --add safe.directory /src

COPY scripts/clone_schema.sql /opt/

WORKDIR /src

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

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

WORKDIR /opt/c2cgeoportal/geoportal
COPY geoportal/package.json geoportal/package-lock.json geoportal/.snyk ./

ENV XDG_CONFIG_HOME=/etc/xdg
RUN chmod ugo+rw /etc/xdg

# hadolint ignore=DL3016,SC2046
RUN --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    npm install --omit=dev --omit=optional --ignore-scripts
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

COPY bin/eval-templates bin/wait-db bin/list4vrt bin/azure /usr/bin/
COPY --from=tools-cleaned /opt/c2cgeoportal /opt/c2cgeoportal
COPY scripts/extract-messages.js /opt/c2cgeoportal/

WORKDIR /opt/c2cgeoportal
RUN --mount=type=cache,target=/var/cache,sharing=locked \
    --mount=type=cache,target=/root/.cache \
    ln -s /opt/c2cgeoportal/commons/c2cgeoportal_commons/alembic /opt \
    && python3 -m pip install --disable-pip-version-check --no-deps \
        --editable=commons \
        --editable=geoportal \
        --editable=admin \
    && python3 -m compileall -q /opt/c2cgeoportal /venv/lib/python3.* \
        -x '(/venv/lib/python3.*/site-packages/(networkx|yaml_include)/|/venv/lib/python3.*/site-packages/c2cgeoform/scaffolds|/opt/c2cgeoportal/geoportal/c2cgeoportal_geoportal/scaffolds/)'

WORKDIR /opt/c2cgeoportal/geoportal

RUN adduser www-data root \
    && pip freeze > /requirements.txt
# From c2cwsgiutils

ENV C2C_BASE_PATH=/c2c \
    C2C_REDIS_TIMEOUT=3 \
    C2C_REDIS_SERVICENAME=mymaster \
    C2C_BROADCAST_PREFIX=broadcast_api_ \
    C2C_SQL_PROFILER_ENABLED=0 \
    C2C_DEBUG_VIEW_ENABLED=0 \
    C2C_ENABLE_EXCEPTION_HANDLING=0

RUN mkdir -p /prometheus-metrics \
    && chmod a+rwx /prometheus-metrics
ENV PROMETHEUS_MULTIPROC_DIR=/prometheus-metrics

# End from c2cwsgiutils

ENV C2CGEOPORTAL_THEME_TIMEOUT=300

#############################################################################################################
# Image that run the checks

FROM tools AS checks

WORKDIR /opt/c2cgeoportal

# For mypy
RUN touch "$(echo /venv/lib/python3.*/site-packages/)/zope/__init__.py" \
    && touch "$(echo /venv/lib/python3.*/site-packages/)/c2c/__init__.py"
