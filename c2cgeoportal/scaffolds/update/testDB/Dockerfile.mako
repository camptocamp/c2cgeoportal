FROM camptocamp/postgresql:pg9.5-latest
MAINTAINER Camptocamp "info@camptocamp.com"

ADD *.sql *.csv *.sh /docker-entrypoint-initdb.d/
