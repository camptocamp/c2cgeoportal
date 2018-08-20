<%namespace file="CONST.mako_inc" import="service_defaults"/>\
---

# A compose file for the build.

version: '2'

volumes:
  build:
    external:
      name: ${build_volume_name}

services:
  config:
    image: ${docker_base}-config:${docker_tag}
    networks:
      - internal

  db:
    image: ${docker_base}-testdb:${docker_tag}
    networks:
      - internal
${service_defaults('db', 5432)}\

  externaldb:
    image: ${docker_base}-external-db:latest
    command: -c log_statement=all
    networks:
      - internal
${service_defaults('externaldb', 5432)}\

  mapserver:
    image: camptocamp/mapserver:7.2
    volumes_from:
      - config:rw
    links:
      - db
    networks:
      - internal
${service_defaults('mapserver', 80)}\

  build:
    image: camptocamp/geomapfish-build:${geomapfish_version}
    volumes:
      - build:/build
      - .:/src
    stdin_open: true
    tty: true
    entrypoint:
      - wait-db-and-run
      - run
    links:
      - db
      - externaldb
      - mapserver
    networks:
      - internal
${service_defaults('geoportal-build', 80)}\
      - HOME_DIR
      - USER_NAME
      - USER_ID
      - GROUP_ID

networks:
  internal:
    internal: true
