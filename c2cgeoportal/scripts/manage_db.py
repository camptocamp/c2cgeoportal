# -*- coding: utf-8 -*-
import os
from optparse import OptionParser
import pkg_resources

from migrate.versioning.shell import main as migrate_main
from paste.deploy import appconfig
import c2cgeoportal

def main():

    usage = """%prog COMMAND ...

    This script is a wrapper to the sqlalchemy-migrate migrate script.

    COMMAND can be any command of sqlalchemy-migrate migrate script. See the
    sqlalchemy-migrate doc for details on its migrate script.

    This script passes the path to the c2cgeoportal migrate repository to the
    underlying migrate command.

    It also adds two options: -c|--app-config and -n|--app-name. These options
    define the target WSGI application.
    The --app-config option defaults to CONST_production.ini.
    The --app-name option is mandatory, unless the value for --app-config is of
    this form: production.ini#mymapp.
    """

    parser = OptionParser(usage=usage)
    parser.disable_interspersed_args()
    parser.add_option('-c', '--app-config', default='CONST_production.ini',
            dest='app_config', help='The application .ini config file')
    parser.add_option('-n', '--app-name', default=None,
            dest='app_name', help='The application name')
    (options, args) = parser.parse_args()

    app_config = options.app_config
    app_name = options.app_name

    if not os.path.isfile(app_config):
        parser.error('Can\'t find config file: %s' % app_config)
    if app_name is None and '#' in app_config:
        app_config, app_name = app_config.split('#', 1)
    if app_name is None:
        parser.error('You must specify the application name using the flag' \
                ' -n|--app-name')

    if '#' in app_config:
        if app_name is None:
            app_config, app_name = app_config.split('#', 1)
        else:
            app_config = app_config.split('#', 1)[0]

    config = appconfig('config:' + options.app_config,
            name=app_name,
            relative_to=os.getcwd()).local_conf

    db_url = config['sqlalchemy.url']
    c2cgeoportal.schema = config['schema']
    repository = pkg_resources.resource_filename(app_name, 'CONST_migration')
    migrate_main(argv=args, url=db_url, repository=repository)
