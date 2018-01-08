---
# A compose file for development.

version: '2'

volumes:
  build:
    external:
      name: ${build_volume_name}

services:
% if dbhost == "db":
  db:
    image: ${docker_base}-testdb:${docker_tag}
    environment:
      POSTGRES_DB: ${db}
      POSTGRES_USER: ${dbuser}
      POSTGRES_PASSWORD: ${dbpassword}
% if development == "TRUE":
    ports:
      - 15432:5432
% endif
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
      - PGHOST=db
      - PGPORT=5432
      - PGUSER=${dbuser}
      - PGPASSWORD=${dbpassword}
      - PGDATABASE=${db}
    stdin_open: true
    tty: true
    entrypoint:
      - wait-for-db
      - run
