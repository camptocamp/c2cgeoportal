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

  db:
    image: ${docker_base}-testdb:${docker_tag}
${service_defaults('db', 5432)}\

  external-db:
    image: ${docker_base}-external-db:latest
${service_defaults('external-db', 5432)}\

  mapserver:
    image: camptocamp/mapserver:7.0
    volumes_from:
      - config:rw
    links:
      - db
${service_defaults('mapserver', 80)}\

  build:
    image: camptocamp/geomapfish-build:${geomapfish_version}
    volumes:
      - build:/build
      - .:/src
    stdin_open: true
    tty: true
    entrypoint:
      - wait-for-db
      - run
    links:
      - db
      - external-db
      - mapserver
${service_defaults('geoportal', 80, True)}\
      - HOME_DIR
      - USER_NAME
      - USER_ID
      - GROUP_ID
