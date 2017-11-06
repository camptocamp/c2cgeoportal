[DEFAULT]
script_location = commons/c2cgeoportal_commons/alembic

sqlalchemy.url = postgresql://${dbuser}:${dbpassword}@${dbhost}:${dbport}/${db}
version_table = c2cgeoportal_version
srid = 21781

[main]
version_table_schema = main
schema = main
version_locations = commons/c2cgeoportal_commons/alembic/main/

[static]
version_table_schema = main_static
main_schema = main
static_schema = main_static
version_locations = commons/c2cgeoportal_commons/alembic/static/

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
