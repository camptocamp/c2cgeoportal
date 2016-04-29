#!/bin/sh -e
#
# variables set here:
#   $TARGET: name of the symbolic remote host key (see remote_hosts
#            section in config file)
#

DATABASES=$@

# Apache must be stopped to prevent database connection during
# databases / tables restore.
sudo apache2ctl stop


# The following line works only with Postgres 9.3 and upper.
# otherwise the schema should be create manually
psql -c 'CREATE SCHEMA IF NOT EXISTS ${schema}_static;' ${db}

psql -c 'CREATE TABLE IF NOT EXISTS ${schema}_static.shorturl (
    id serial PRIMARY KEY,
    url character varying(1000),
    ref character varying(20) NOT NULL UNIQUE,
    creator_email character varying(200),
    creation timestamp without time zone,
    last_hit timestamp without time zone,
    nb_hits integer
);' ${db}

psql -c 'GRANT USAGE ON SCHEMA "${schema}_static" TO "${dbuser}";' ${db}
psql -c 'GRANT SELECT ON ALL TABLES IN SCHEMA "${schema}_static" TO "${dbuser}";' ${db}

cd "${directory}"
.build/venv/bin/alembic -c alembic_static.ini upgrade head
