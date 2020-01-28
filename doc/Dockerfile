FROM debian:stretch

RUN apt-get update
RUN apt-get install --assume-yes --no-install-recommends python3-pip python3-setuptools gettext

RUN python3 -m pip install --disable-pip-version-check --no-cache-dir wheel pipenv

COPY Pipfile Pipfile.lock /tmp/
RUN \
  cd /tmp && LC_ALL=C.UTF-8 LANG=C.UTF-8 pipenv install --system --deploy --clear

ARG MAJOR_VERSION
ARG MAIN_BRANCH

COPY . /doc
WORKDIR /doc

RUN ./eval-templates
RUN  mkdir --parent _build/html
RUN  ./build.sh
