---
# A compose file for development.

version: '2'

volumes:
  build:
    external:
      name: ${build_volume_name}

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

  mapserver:
    image: ${docker_base}-mapserver:${docker_tag}
% if development == "TRUE":
    ports:
      - 8380:80
% endif

  build:
    image: camptocamp/geomapfish-build:${geomapfish_version}
    volumes:
      - build:/build
      - .:/src
    environment:
      - USER_NAME
      - USER_ID
      - GROUP_ID
      - VISIBLE_WEB_HOST=-
      - VISIBLE_WEB_PROTOCOL=-
      - VISIBLE_ENTRY_POINT=-
      - PGHOST=db
      - PGHOST_SLAVE=db
      - PGPORT=5432
      - PGUSER=www-data
      - PGPASSWORD=www-data
      - PGDATABASE=geomapfish
      - PGSCHEMA=main
      - PGSCHEMA_STATIC=main_static
      - TINYOWS_URL=http://tinyows/
      - MAPSERVER_URL=http://mapserver/
      - PRINT_URL=http://print:8080/print/
    stdin_open: true
    tty: true
    entrypoint:
      - wait-for-db
      - run
    links:
      - db
      - mapserver
