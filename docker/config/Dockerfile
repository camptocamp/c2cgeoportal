FROM ubuntu:22.04
LABEL maintainer Camptocamp "info@camptocamp.com"
SHELL ["/bin/bash", "-o", "pipefail", "-cux"]

ARG VERSION
ENV VERSION=$VERSION

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update \
    && apt-get upgrade --assume-yes \
    && apt-get install --assume-yes --no-install-recommends gettext-base python3

COPY bin/ /usr/bin/
COPY haproxy/ /etc/haproxy/
COPY haproxy_dev/ /etc/haproxy_dev/

ENTRYPOINT [ "/usr/bin/entrypoint" ]
