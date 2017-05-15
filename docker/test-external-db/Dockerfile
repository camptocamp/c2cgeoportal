FROM camptocamp/postgres:latest

ENV POSTGRES_USER www-data
ENV POSTGRES_DB test

ADD *.sql /docker-entrypoint-initdb.d
