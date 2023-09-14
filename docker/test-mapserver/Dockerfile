FROM camptocamp/mapserver:7.6-gdal3.3
LABEL maintainer Camptocamp "info@camptocamp.com"

RUN \
  apt-get update && \
  apt-get install --assume-yes --no-install-recommends gettext && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

COPY eval-templates /usr/bin/
COPY *.map.tmpl /etc/mapserver/

ENTRYPOINT ["/usr/bin/eval-templates"]
CMD ["/usr/local/bin/start-server"]
