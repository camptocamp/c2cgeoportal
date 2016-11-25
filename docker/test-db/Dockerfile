FROM camptocamp/postgresql:latest

ENV POSTGRES_USER www-data
ENV POSTGRES_DB geomapfish

ADD *.sql /docker-entrypoint-initdb.d
