---
# A compose file for development.

version: '2'

volumes:
  build:
    external:
      name: ${build_volume_name}

services:
% if dbhost == "db":
  db:
    image: ${docker_base}-testdb:${docker_tag}
    environment:
      POSTGRES_DB: geomapfish
      POSTGRES_USER: www-data
      POSTGRES_PASSWORD: www-data
% if development == "TRUE":
    ports:
      - 15432:5432
% endif
% endif

  build:
    image: camptocamp/geomapfish-build:${geomapfish_version}
    volumes:
      - build:/build
      - .:/src
    environment:
      - USER_NAME
      - USER_ID
      - GROUP_ID
    stdin_open: true
    tty: true
    command: ${'$'}{RUN}
