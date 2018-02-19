---
# A compose file for development.
version: '2'
services:
  db:
    image: camptocamp/testgeomapfish-testdb:latest
    environment:
      POSTGRES_USER: www-data
      POSTGRES_PASSWORD: www-data
      POSTGRES_DB: geomapfish

  external-db:
    image: camptocamp/testgeomapfish-external-db:latest
    environment:
      POSTGRES_USER: www-data
      POSTGRES_PASSWORD: www-data
      POSTGRES_DB: test

  print:
    image: camptocamp/testgeomapfish-print:latest

  mapserver:
    image: camptocamp/testgeomapfish-mapserver:latest

  geoportal:
    image: camptocamp/testgeomapfish-geoportal:latest
    ports:
      - 8080:80
    environment:
      PGHOST: db
      PGHOST_SLAVE: db
      PGPORT: 5432
      PGUSER: www-data
      PGPASSWORD: www-data
      PGDATABASE: geomapfish
      PGSCHEMA: main
      PGSCHEMA_STATIC: main_static
      VISIBLE_WEB_HOST: localhost:8080
      VISIBLE_WEB_PROTOCOL: http
      VISIBLE_ENTRY_POINT: /
      TINYOWS_URL: http://tinyows/
      MAPSERVER_URL: http://mapserver/
      PRINT_URL: http://print:8080/print/
