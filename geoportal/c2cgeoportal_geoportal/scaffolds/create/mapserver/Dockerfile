FROM camptocamp/mapserver:7.0
LABEL maintainer Camptocamp "info@camptocamp.com"

COPY . /etc/mapserver/
COPY replace_db.sh /docker-entrypoint.d/01_replace_db.sh
