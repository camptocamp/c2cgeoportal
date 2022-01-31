FROM camptocamp/geomapfish-tools

COPY Pipfile Pipfile.lock /tmp/
RUN \
  cd /tmp && LC_ALL=C.UTF-8 LANG=C.UTF-8 pipenv sync --system --clear

ARG MAJOR_VERSION
ARG MAIN_BRANCH

COPY . /doc
WORKDIR /doc

RUN  mkdir --parent _build/html
RUN sphinx-build -b html -d _build/doctrees . _build/html
RUN  ./build.sh
