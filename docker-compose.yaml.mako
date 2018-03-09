---

db:
  image: camptocamp/geomapfish-test-db:latest
  environment:
    - POSTGRES_USER=www-data
    - POSTGRES_PASSWORD=www-data
    - POSTGRES_DB=geomapfish_tests

mapserver:
  image: camptocamp/geomapfish-test-mapserver:latest
  links:
    - db

build:
  image: camptocamp/geomapfish-build:${major_version}
  volumes:
    - ${build_volume_name}:/build
    - .:/src
  environment:
    - USER_NAME
    - USER_ID
    - GROUP_ID
    - CI
    - PGHOST=db
    - PGPORT=5432
    - PGUSER=www-data
    - PGPASSWORD=www-data
    - PGDATABASE=geomapfish_tests
  stdin_open: true
  tty: true
  entrypoint:
    - wait-for-db
    - run
  links:
    - db
    - mapserver
