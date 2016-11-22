FROM camptocamp/postgis:9.4

ENV POSTGRES_USER www-data
ENV POSTGRES_DB geomapfish

ADD *.sql /docker-entrypoint-initdb.d
