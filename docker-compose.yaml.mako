version: '2.1'

volumes:
  ${build_volume_name}:

services:
  db:
    image: camptocamp/geomapfish-test-db:latest
    environment:
      - POSTGRES_USER=www-data
      - POSTGRES_PASSWORD=www-data
      - POSTGRES_DB=geomapfish_tests
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 3

  mapserver:
    image: camptocamp/geomapfish-test-mapserver:latest
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
    depends_on:
      db:
        condition: service_healthy
