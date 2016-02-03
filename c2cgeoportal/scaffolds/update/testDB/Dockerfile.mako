FROM camptocamp/postgis:9.5
MAINTAINER Camptocamp "info@camptocamp.com"

ENV POSTGRES_USER ${dbuser}
ENV POSTGRES_DB ${db}
ADD *.sql *.csv *.sh /docker-entrypoint-initdb.d/
