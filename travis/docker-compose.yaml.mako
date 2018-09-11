<%namespace file="CONST.mako_inc" import="service_defaults"/>\
---

# The project Docker compose file for development.

version: '2'
services:
  config:
    image: ${docker_base}-config:${docker_tag}
    user: www-data
    networks:
      - internal
${service_defaults('config')}\

  db:
    image: ${docker_base}-testdb:${docker_tag}
    networks:
      - internal
${service_defaults('db', 5432)}\

  externaldb:
    image: camptocamp/testgeomapfish-external-db:latest
    command: -c log_statement=all
    networks:
      - internal
${service_defaults('externaldb', 5432)}\

  print:
    image: camptocamp/mapfish_print:3.16
    user: www-data
    volumes_from:
      - config:ro
    networks:
      - internal
${service_defaults('print', 8080)}\

  mapserver:
    image: camptocamp/mapserver:7.2
    user: www-data
    volumes_from:
      - config:rw
    entrypoint: []
    networks:
      - internal
${service_defaults('mapserver', 80)}\

  redis:
    image: redis:3.2
    user: www-data
    networks:
      - internal
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
    image: camptocamp/tilecloud-chain:1.7
    user: www-data
    volumes_from:
      - config:ro
    networks:
      - internal
${service_defaults('tilecloudchain', 8080)}\

  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
    user: www-data
    networks:
      - internal
${service_defaults('geoportal', 8080)}\


  front:
    image: haproxy:1.8.8
    volumes_from:
      - config:ro
    volumes:
      - /dev/log:/dev/log:rw
    command:
      - haproxy
      - -f
      - /etc/haproxy
    networks:
      - internal
${service_defaults('front', 80, True)}

networks:
  internal:
    internal: true
