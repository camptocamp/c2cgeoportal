FROM camptocamp/geomapfish-tools

COPY Pipfile Pipfile.lock /tmp/
RUN \
  cd /tmp && LC_ALL=C.UTF-8 LANG=C.UTF-8 pipenv sync --system --clear

# To be removed when tilecloudchain will use c2cwsgiutils 5.0
RUN mkdir -p /usr/local/lib/python3.8/dist-packages/tilecloud_chain/ && \
    curl https://raw.githubusercontent.com/camptocamp/tilecloud-chain/master/tilecloud_chain/USAGE.rst -o \
    /usr/local/lib/python3.8/dist-packages/tilecloud_chain/USAGE.rst && \
    curl https://raw.githubusercontent.com/camptocamp/tilecloud-chain/master/tilecloud_chain/schema.json -o \
    /usr/local/lib/python3.8/dist-packages/tilecloud_chain/schema.json

ARG MAJOR_VERSION
ARG MAIN_BRANCH

COPY . /doc
WORKDIR /doc

RUN  mkdir --parent _build/html
RUN sphinx-build -b html -d _build/doctrees . _build/html
RUN  ./build.sh
