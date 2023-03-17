FROM debian:stretch
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN \
    apt-get update \
    && apt-get install --assume-yes --no-install-recommends gettext-base python3 \
    && apt-get clean \
    && rm --recursive --force /var/lib/apt/lists/*
