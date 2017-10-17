version: '2'

volumes:
    c2cgpbuild:
        external:
            name: ${build_volume_name}

services:

    db:
        build: docker/gis-db
        image: camptocamp/c2cgeoportal-gis-db
        environment:
        - POSTGRES_USER=www-data
        - POSTGRES_PASSWORD=www-data
        - POSTGRES_DB=geomapfish_test

    mapserver:
        build: docker/test-mapserver
        image: camptocamp/c2cgeoportal-test-mapserver

    build:
        image: camptocamp/geomapfish-build-dev:2.3
        volumes:
        - c2cgpbuild:/build
        - .:/src
        environment:
        - USER_NAME
        - USER_ID
        - GROUP_ID
        stdin_open: true
        tty: true
        command: ${'$'}{RUN}
