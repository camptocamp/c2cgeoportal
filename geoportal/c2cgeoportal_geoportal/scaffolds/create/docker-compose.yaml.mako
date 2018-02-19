---
# A compose file for development.
version: '2'
services:
  db:
    image: ${docker_base}-testdb:${docker_tag}
    environment:
      POSTGRES_DB: geomapfish
      POSTGRES_USER: www-data
      POSTGRES_PASSWORD: www-data
% if development == "TRUE":
    ports:
      - 15432:5432
% endif

  print:
    image: ${docker_base}-print:${docker_tag}
% if development == "TRUE":
    ports:
      - 8280:8080
% endif

  mapserver:
    image: ${docker_base}-mapserver:${docker_tag}
% if development == "TRUE":
    ports:
      - 8380:80
% endif

  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
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
