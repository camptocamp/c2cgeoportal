<%namespace file="CONST.mako_inc" import="service_defaults"/>\
---

# The project Docker compose file for development.

version: '2'
services:
  config:
    image: ${docker_base}-config:${docker_tag}
    user: www-data
${service_defaults('config')}\

  db:
    image: ${docker_base}-testdb:${docker_tag}
${service_defaults('db', 5432)}\

  external-db:
    image: camptocamp/testgeomapfish-external-db:latest
${service_defaults('external-db', 5432)}\

  print:
    image: camptocamp/mapfish_print:3.15
    user: www-data
    volumes_from:
      - config:ro
${service_defaults('print', 8080)}\

  mapserver:
    image: camptocamp/mapserver:7.2
    user: www-data
    volumes_from:
      - config:rw
    entrypoint: []
${service_defaults('mapserver', 80)}\

  redis:
    image: redis:3.2
    user: www-data
${service_defaults('mapserver', 6379)}\

  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
    user: www-data
${service_defaults('geoportal', 8080, True)}\
