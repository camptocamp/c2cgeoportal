FROM camptocamp/mapserver:8.0-gdal3.6
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN --mount=type=cache,target=/var/lib/apt/lists \
    --mount=type=cache,target=/var/cache,sharing=locked \
    apt-get update \
    && apt-get install --assume-yes --no-install-recommends gettext

COPY eval-templates /usr/bin/
COPY *.map.tmpl /etc/mapserver/
RUN chmod go+w /etc/mapserver

ENTRYPOINT ["/usr/bin/eval-templates"]
CMD ["/usr/local/bin/start-server"]
