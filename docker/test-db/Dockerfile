FROM camptocamp/postgres:9.5

LABEL maintainer Camptocamp "info@camptocamp.com"

COPY *.sql /docker-entrypoint-initdb.d/

ENV \
    POSTGRES_DB=geomapfish \
    POSTGRES_USER=www-data \
    POSTGRES_PASSWORD=www-data
