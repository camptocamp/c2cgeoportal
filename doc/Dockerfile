FROM camptocamp/geomapfish-tools

# Fail on error on pipe, see: https://github.com/hadolint/hadolint/wiki/DL4006.
# Treat unset variables as an error when substituting.
# Print commands and their arguments as they are executed.
SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

RUN . /etc/os-release \
    && apt-get update \
    && apt-get install --assume-yes --no-install-recommends curl gnupg \
    && echo "deb https://deb.nodesource.com/node_16.x ${VERSION_CODENAME} main" > /etc/apt/sources.list.d/nodesource.list \
    && curl --silent https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - \
    && apt-get update \
    && apt-get install --assume-yes --no-install-recommends 'nodejs=16.*'

COPY Pipfile Pipfile.lock /tmp/
RUN \
    cd /tmp && LC_ALL=C.UTF-8 LANG=C.UTF-8 pipenv sync --system --clear

# To be removed when tilecloudchain will use c2cwsgiutils 5.0
RUN mkdir -p /usr/local/lib/python3.8/dist-packages/tilecloud_chain/ \
    && curl https://raw.githubusercontent.com/camptocamp/tilecloud-chain/master/tilecloud_chain/USAGE.rst -o \
        /usr/local/lib/python3.8/dist-packages/tilecloud_chain/USAGE.rst \
    && curl https://raw.githubusercontent.com/camptocamp/tilecloud-chain/master/tilecloud_chain/schema.json -o \
        /usr/local/lib/python3.8/dist-packages/tilecloud_chain/schema.json

COPY package.json /doc/
RUN cd /doc && npm install

COPY . /doc
WORKDIR /doc

ARG MAJOR_VERSION
ARG MAIN_BRANCH

RUN ./import_ngeo_config.py --type Configuration integrator/ngeo_configuration.rst \
    --type APIConfig integrator/ngeo_api_configuration.rst \
    node_modules/ngeo/dist/typedoc.json integrator/ngeo_other_configuration.rst \
    && mkdir --parent _build/html \
    && sphinx-build -b html -d _build/doctrees . _build/html \
    && ./build.sh
