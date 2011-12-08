# -*- coding: utf-8 -*-
import warnings
from optparse import OptionParser
import pkg_resources

from migrate.versioning.shell import main
from paste.deploy import appconfig

def main():
    # Ignores pyramid deprecation warnings
    warnings.simplefilter('ignore', DeprecationWarning) 

    usage = """%prog COMMAND ...

    This script is a wrapper to the sqlalchemy-migrate migrate script.

    COMMAND can be any command of sqlalchemy-migrate migrate script. See the
    sqlalchemy-migrate doc for details on its migrate script.

    This script passes the path to the c2cgeoportal migrate repository to the
    underlying migrate command.

    It also adds the option: -c|--app-config. This option refers to the paste
    configuration file of the target WSGI application. The script then parse
    that config to find out the sqlalchemy.url value.
    """

    parser = OptionParser(usage=usage)
    parser.add_option('-c', '--app-config', default='CONST_production.ini',
                      dest='app_config', help='The application config file')
    (options, args) = parser.parse_args()

    config = appconfig('config:' + options.app_config, name='${package}')

    db_url = config.local_conf['sqlalchemy.url']
    repository = pkg_resources.resource_filename('${package}', 'CONST_migration')
    main(url=db_url, repository=repository)
