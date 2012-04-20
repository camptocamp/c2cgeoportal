# -*- coding: utf-8 -*-
import os
from optparse import OptionParser, SUPPRESS_HELP
import pkg_resources

from migrate.versioning.shell import main as migrate_main
from paste.deploy import appconfig
import c2cgeoportal


def main():

    usage = "The wrapper adds two options to define the target WSGI application."

    parser = OptionParser(usage=usage, add_help_option=False)
    parser.disable_interspersed_args()
    parser.add_option('-h', '--help', dest='help', action="store_true", help=SUPPRESS_HELP)
    parser.add_option('-c', '--app-config', default='production.ini',
            dest='app_config', help='The application .ini config file')
    parser.add_option('-n', '--app-name', default=None,
            dest='app_name', help='The application name')
    (options, args) = parser.parse_args()

    # display help
    if options.help or \
            len(args) == 1 and args[0] == 'help' or \
            len(args) == 0:
        print """This script is a wrapper to the sqlalchemy-migrate migrate script.

This script passes the path to the c2cgeoportal migrate repository to the
underlying migrate command.
"""

        migrate_main(["help"])
        print
        parser.print_help()
        return

    # display sqlalchemy-migrate command help
    if args[0] == 'help':
        migrate_main(argv=args)
        return

    app_config = options.app_config
    app_name = options.app_name

    if app_name is None and '#' in app_config:
        app_config, app_name = app_config.split('#', 1)
    if not os.path.isfile(app_config):
        parser.error('Can\'t find config file: %s' % app_config)
    if app_name is None:
        parser.error('You must specify the application name using the flag' \
                ' -n|--app-name')

    config = appconfig('config:' + options.app_config,
            name=app_name,
            relative_to=os.getcwd()).local_conf

    db_url = config['sqlalchemy.url']
    c2cgeoportal.schema = config['schema']
    repository = pkg_resources.resource_filename(app_name, 'CONST_migration')
    migrate_main(argv=args, url=db_url, repository=repository)
