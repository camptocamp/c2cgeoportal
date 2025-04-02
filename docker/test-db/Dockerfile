FROM ghcr.io/camptocamp/postgres:17-postgis-3

LABEL org.opencontainers.image.authors="Camptocamp <info@camptocamp.com>"

COPY *.sql /docker-entrypoint-initdb.d/

ENV \
    POSTGRES_DB=geomapfish \
    POSTGRES_USER=www-data \
    POSTGRES_PASSWORD=www-data
