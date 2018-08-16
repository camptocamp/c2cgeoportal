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

  mapserver:
    image: camptocamp/mapserver:7.2
    user: www-data
    entrypoint: []
    volumes_from:
      - config:rw
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
      - mapserver
${service_defaults('geoportal-build', 80)}\
      - HOME_DIR
      - USER_NAME
      - USER_ID
      - GROUP_ID
