<%namespace file="CONST.mako_inc" import="service_defaults"/>\
---

# The project Docker compose file for development.

version: '2'
services:
  config:
    image: ${docker_base}-config:${docker_tag}
${service_defaults('config')}\

  print:
    image: camptocamp/mapfish_print:3.12.1
    volumes_from:
      - config:ro
${service_defaults('print', 8080)}\

  mapserver:
    image: camptocamp/mapserver:7.0
    volumes_from:
      - config:rw
    volumes:
      - /var/sig:/var/sig:ro
    entrypoint: []
${service_defaults('mapserver', 80)}\

##  qgisserver:
##    image: camptocamp/qgis-server:latest
##    volumes_from:
##      - config:ro
##${service_defaults('qgisserver', 80)}

  mapcache:
    image: camptocamp/mapcache:1.6
    volumes_from:
      - config:ro
${service_defaults('mapcache', 80)}\

  memcached:
    image: memcached:1.5
${service_defaults('memcached', 11211)}\

  redis:
    image: redis:3.2
${service_defaults('redis', 6379)}\

  tilecloudchain:
    image: camptocamp/tilecloud-chain:1.6
    volumes_from:
      - config:ro
${service_defaults('tilecloudchain', 80)}\

  tilegeneration:
    image: camptocamp/tilecloud-chain:1.6
    volumes_from:
      - config:ro
${service_defaults('tilecloudchain')}\
    entrypoint:
      - bash
      - -c
      - sleep infinity

  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
    volumes:
      - /var/sig:/var/sig:ro
${service_defaults('geoportal', 80)}\

  front:
    image: haproxy:1.8
    volumes_from:
      - config:ro
    volumes:
      - /dev/log:/dev/log:rw
    command: ["haproxy", "-f", "/etc/haproxy"]
${service_defaults('front', 80, not docker_global_front)}
%if docker_global_front:
    networks:
      default: {}
      global:
        aliases:
          - ${instance}
%endif

%if docker_global_front:
networks:
  default: {}
  global:
    external:
      name: global_default
%endif
