FROM camptocamp/postgres:11

LABEL maintainer Camptocamp "info@camptocamp.com"

COPY *.sql /docker-entrypoint-initdb.d

ENV \
    POSTGRES_DB=test \
    POSTGRES_USER=www-data \
    POSTGRES_PASSWORD=www-data
