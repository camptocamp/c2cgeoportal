---
<%def name="defaults(service, inner_port, port_required=False)">
% if 'environment' in docker_services.get(service, {}):
    environment:
% for key, value in docker_services[service]['environment'].items():
      ${key}: ${repr(value)}
% endfor
% endif
% if port_required or 'port' in docker_services.get(service, {}):
    ports:
      - ${docker_services[service]['port']}:${inner_port}
% endif
</%def>
# The project Docker compose file.
version: '2'
services:
  db:
    image: ${docker_base}-testdb:${docker_tag}
${defaults('db', 5432)}

  print:
    image: ${docker_base}-print:${docker_tag}
${defaults('print', 8080)}

  mapserver:
    image: ${docker_base}-mapserver:${docker_tag}
${defaults('mapserver', 80)}


  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
${defaults('geoportal', 80, True)}
