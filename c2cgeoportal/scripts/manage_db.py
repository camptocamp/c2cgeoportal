# -*- coding: utf-8 -*-

import warnings
import pkg_resources

from migrate.versioning.shell import main

from pyramid.paster import get_app

def run():

    # Ignores pyramid deprecation warnings
    warnings.simplefilter('ignore', DeprecationWarning) 

    usage = """%%prog COMMAND ...

    This script is a wrapper to the sqlalchemy-migrate migrate script.

    COMMAND can be any command of sqlalchemy-migrate migrate script. See the
    sqlalchemy-migrate doc for details on its migrate script.

    This script passes the path to the c2cgeoportal migrate repository to the
    underlying migrate command.

    It also adds two options: -c|--app-config and -n|--app-name. These options
    define the target WSGI application. The --app-config option is mandatory. The
    --app-name option is mandatory, unless the value for --app-config is of
    this form: production.ini#mymapp.
    """

    parser = optparse.OptionParser()
    parser.add_option('-c', '--app-config', default='CONST_production.ini',
                      dest='app_config', help='The application config file')
    parser.add_option('-n', '--app-name', default=None,
                      dest='app_name', help='The application name')
    (options, args) = parser.parse_args()

    app_config = options.app_config
    app_name = options.app_name

    if '#' in app_config:
        if app_name is None:
            app_config, app_name = app_config.split('#', 1)
        else:
            app_config = app_config.split('#', 1)[0]

    app = get_app(app_config, app_name)
    db = app.registry.settings['sqlalchemy.url']

    repository = pkg_resources.resource_filename('c2cgeoportal', 'migration')

    main(url=db, repository=repository)
