---

db:
  image: camptocamp/c2cgeoportal-gis-db:latest
  environment:
    - POSTGRES_USER=www-data
    - POSTGRES_PASSWORD=www-data
    - POSTGRES_DB=geomapfish_tests

mapserver:
  image: camptocamp/c2cgeoportal-test-mapserver:latest
  links:
    - db

build:
  image: camptocamp/geomapfish-admin-build:${major_version}
  volumes:
    - ${build_volume_name}:/build
    - .:/src
  environment:
    - USER_NAME
    - USER_ID
    - GROUP_ID
    - CI
  stdin_open: true
  tty: true
  command: ${'$'}{RUN}
  links:
    - db
    - mapserver
