FROM debian:stretch
LABEL maintainer Camptocamp "info@camptocamp.com"

ARG VERSION
ENV VERSION=$VERSION

RUN \
    apt-get update \
    && apt-get install --assume-yes --no-install-recommends gettext-base python3 \
    && apt-get clean \
    && rm --recursive --force /var/lib/apt/lists/*

COPY gunicorn_config.py /etc/gunicorn/config.py
COPY bin/ /usr/bin/
COPY haproxy/ /etc/haproxy/
COPY haproxy_dev/ /etc/haproxy_dev/

ENTRYPOINT [ "/usr/bin/entrypoint" ]
