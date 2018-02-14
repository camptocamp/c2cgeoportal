---
# A compose file for development.
version: '2'
services:
  db:
    image: ${docker_base}-testdb:${docker_tag}
% if 'environment' in docker_services.get('db', {}):
    environment:
% for key, value in docker_services['db']['environment'].items():
      ${key}: ${value}
% endfor
% endif
% if 'port' in docker_services.get('db', {}):
    ports:
      - ${docker_services['db']['port']}:5432
% endif

  print:
    image: ${docker_base}-print:${docker_tag}
% if 'environment' in docker_services.get('print', {}):
    environment:
% for key, value in docker_services['print']['environment'].items():
      ${key}: ${value}
% endfor
% endif
% if 'port' in docker_services.get('print', {}):
    ports:
      - ${docker_services['print']['port']}:8080
% endif

  mapserver:
    image: ${docker_base}-mapserver:${docker_tag}
% if 'environment' in docker_services.get('mapserver', {}):
    environment:
% for key, value in docker_services['mapserver']['environment'].items():
      ${key}: ${value}
% endfor
% endif
% if 'port' in docker_services.get('mapserver', {}):
    ports:
      - ${docker_services['mapserver']['port']}:80
% endif
% if development == "TRUE":
    ports:
      - 8380:80
% endif

  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
% if 'environment' in docker_services.get('geoportal', {}):
    environment:
% for key, value in docker_services['geoportal']['environment'].items():
      ${key}: ${value}
% endfor
% endif
    ports:
      - ${docker_services['geoportal']['port']}:80
