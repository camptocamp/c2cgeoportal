<%namespace file="CONST.mako_inc" import="service_defaults"/>\
---

# The project Docker compose file for development.

version: '2'
services:
  config:
    image: ${docker_base}-config:${docker_tag}

  print:
    image: camptocamp/mapfish_print:3.12.1
    volumes_from:
      - config:ro
${service_defaults('print', 8080)}\

  mapserver:
    image: camptocamp/mapserver:7.0
    volumes_from:
      - config:rw
${service_defaults('mapserver', 80)}\

##  qgisserver:
##    image: camptocamp/geomapfish-qgisserver
##    volumes_from:
##      - config:ro
##${service_defaults('mapserver', 80)}

  mapcache:
    image: camptocamp/mapcache:1.6
    volumes_from:
      - config:ro
${service_defaults('mapserver', 80)}\

  memcached:
    image: memcached:1.5
${service_defaults('mapserver', 11211)}\

  redis:
    image: redis:3.2
${service_defaults('mapserver', 6379)}\

  tilecloudchain:
    image: camptocamp/tilecloud-chain:1.5.0
    volumes_from:
      - config:ro
${service_defaults('mapserver', 80)}\

  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
${service_defaults('geoportal', 80)}\

  front:
    image: haproxy:1.8
    volumes_from:
      - config:ro
    volumes:
      - /dev/log:/dev/log:rw
    command: ["haproxy", "-f", "/etc/haproxy"]
${service_defaults('front', 80, True)}
