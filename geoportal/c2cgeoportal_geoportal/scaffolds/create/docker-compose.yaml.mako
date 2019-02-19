<%namespace file="CONST.mako_inc" import="service_defaults"/>\
---

# The project Docker compose file for development.

version: '2'

services:
  config:
    image: ${docker_base}-config:${docker_tag}
    user: www-data
${service_defaults('config')}\

  print:
    image: camptocamp/mapfish_print:3.16
    user: www-data
    restart: unless-stopped
    volumes_from:
      - config:ro
${service_defaults('print', 8080)}\

  mapserver:
    image: camptocamp/mapserver:7.2
    user: www-data
    restart: unless-stopped
    volumes_from:
      - config:rw
    volumes:
      - /var/sig:/var/sig:ro
    entrypoint: []
${service_defaults('mapserver', 8080)}\

##  qgisserver:
##    image: camptocamp/geomapfish-qgisserver:gmf2.3-qgis3.2
##    user: www-data
##    restart: unless-stopped
##    volumes_from:
##      - config:ro
##${service_defaults('qgisserver', 8080)}

  tinyows:
    image: camptocamp/tinyows
    user: www-data
    restart: unless-stopped
    volumes_from:
      - config:ro
${service_defaults('tinyows', 8080)}\

  mapcache:
    image: camptocamp/mapcache:1.6
    user: www-data
    restart: unless-stopped
    volumes_from:
      - config:ro
${service_defaults('mapcache', 8080)}\

  memcached:
    image: memcached:1.5
    user: www-data
    restart: unless-stopped
    command:
      - memcached
      - --memory-limit=512
${service_defaults('memcached', 11211)}\

  redis:
    image: redis:3.2
    user: www-data
    restart: unless-stopped
    command:
      - redis-server
      - --save
      - ''
      - --appendonly
      - 'no'
      - --maxmemory
      - 512mb
      - --maxmemory-policy
      - allkeys-lru
${service_defaults('redis', 6379)}\

  tilecloudchain:
    image: camptocamp/tilecloud-chain:1.9
    user: www-data
    restart: unless-stopped
    volumes_from:
      - config:ro
${service_defaults('tilecloudchain', 8080)}\

  tilegeneration_slave:
    image: camptocamp/tilecloud-chain:1.9
    user: www-data
    restart: unless-stopped
    volumes_from:
      - config:ro
${service_defaults('tilecloudchain')}\
    entrypoint:
      - generate_tiles
      - --role=slave

  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
    user: www-data
    restart: unless-stopped
    volumes:
      - /var/sig:/var/sig:ro
${service_defaults('geoportal', 8080)}\

  alembic:
    image: ${docker_base}-geoportal:${docker_tag}
    user: www-data
    command:
      - alembic
      - --name=static
      - upgrade
      - head
${service_defaults('geoportal')}\

  front:
    image: haproxy:1.8.8
    restart: unless-stopped
    volumes_from:
      - config:ro
    volumes:
      - /dev/log:/dev/log:rw
    command:
      - haproxy
      - -f
      - /etc/haproxy
${service_defaults('front', 80, True, docker_global_front)}
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
