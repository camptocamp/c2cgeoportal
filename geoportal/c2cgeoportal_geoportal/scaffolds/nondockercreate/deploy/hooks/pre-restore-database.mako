#!/bin/sh -ex
#
# variables set here:
#   $TARGET: name of the symbolic remote host key (see remote_hosts
#            section in config file)
#

DATABASES=$@

cd ${deploy["code_destination"]}

# Apache must be stopped to prevent database connection during
# databases / tables restore.
sudo service apache2 stop

if psql --list --tuples-only | cut --delimiter='|' --fields=1 | grep --quiet --fixed-strings $DATABASES; then
    printf ""
else
    sudo -u postgres createdb $DATABASES --template template_postgis
fi

# The following line works only with Postgres 9.3 and upper.
# otherwise the schema should be create manually
psql -c 'CREATE SCHEMA IF NOT EXISTS ${schema_static};' ${db}

psql -c 'CREATE TABLE IF NOT EXISTS ${schema_static}.shorturl (
    id serial PRIMARY KEY,
    url character varying(1000),
    ref character varying(20) NOT NULL UNIQUE,
    creator_email character varying(200),
    creation timestamp without time zone,
    last_hit timestamp without time zone,
    nb_hits integer
);' ${db}

psql -c 'GRANT ALL ON SCHEMA "${schema_static}" TO "${dbuser}";' ${db}
psql -c 'GRANT ALL ON ALL TABLES IN SCHEMA "${schema_static}" TO "${dbuser}";' ${db}
psql -c 'ALTER TABLE main_static.shorturl OWNER TO "www-data";' ${db}

./docker-run make --makefile=$TARGET.mk geoportal/alembic.ini geoportal/alembic.yaml
./docker-run alembic --name=static upgrade head
