---
# A compose file for development.
version: '2'
services:
% if dbhost == "db":
  db:
    image: ${docker_base}-testdb:${docker_tag}
    environment:
      POSTGRES_USER: ${dbuser}
      POSTGRES_DB: ${db}
      POSTGRES_PASSWORD: ${dbpassword}
% if development == "TRUE":
    ports:
      - 15432:5432
% endif
% endif

  print:
    image: ${docker_base}-print:${docker_tag}
% if development == "TRUE":
    ports:
      - 8280:8080
% endif

  mapserver:
    image: ${docker_base}-mapserver:${docker_tag}
% if development == "TRUE":
    ports:
      - 8380:80
% endif

  geoportal:
    image: ${docker_base}-geoportal:${docker_tag}
    ports:
      - 8080:80
