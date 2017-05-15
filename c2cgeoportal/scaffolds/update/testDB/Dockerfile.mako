FROM camptocamp/postgis:9.5

LABEL maintainer Camptocamp "info@camptocamp.com"

COPY *.sql *.csv *.sh /docker-entrypoint-initdb.d/
