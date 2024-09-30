FROM camptocamp/postgres:16-postgis-3

LABEL maintainer Camptocamp "info@camptocamp.com"

COPY *.sql /docker-entrypoint-initdb.d/

ENV \
    POSTGRES_DB=geomapfish \
    POSTGRES_USER=www-data \
    POSTGRES_PASSWORD=www-data
