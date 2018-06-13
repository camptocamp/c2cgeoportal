<%namespace file="CONST.mako_inc" import="service_defaults"/>\
---

# The project Docker compose file for development.

version: '2'

services:

  webpack-dev-server:
    image: ${docker_base}-geoportal:${docker_tag}
    volumes:
      - ${project_directory}/geoportal/${package}_geoportal/static-ngeo:/app/${package}_geoportal/static-ngeo
    environment:
      - INTERFACE=desktop
    command:
      - webpack-dev-server
      - --mode=development
      - --port=8080
      - --debug
      - --watch
      - --progress
