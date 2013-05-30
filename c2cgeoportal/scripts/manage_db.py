# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import os
from optparse import OptionParser, SUPPRESS_HELP
import pkg_resources

from migrate.versioning.shell import main as migrate_main
from paste.deploy import appconfig
import c2cgeoportal


def main():

    usage = 'The wrapper adds two options to define ' \
            'the target WSGI application.'

    parser = OptionParser(usage=usage, add_help_option=False)
    parser.disable_interspersed_args()
    parser.add_option('-h', '--help', dest='help', action="store_true",
                      help=SUPPRESS_HELP)
    _help = 'The application .ini config file (optional, ' \
            'default is production.ini)'
    parser.add_option('-c', '--app-config', default='production.ini',
                      dest='app_config', help=_help)
    _help = 'The application name (optional, default is "app")'
    parser.add_option('-n', '--app-name', default="app",
                      dest='app_name', help=_help)
    (options, args) = parser.parse_args()

    # display help
    if options.help or \
            len(args) == 1 and args[0] == 'help' or \
            len(args) == 0:
        print """
This script is a wrapper to the sqlalchemy-migrate migrate script.

This script passes the path to the c2cgeoportal migrate repository to the
underlying migrate command.
"""

        migrate_main(["help"])
        print
        parser.print_help()
        return

    app_config = options.app_config
    app_name = options.app_name

    if app_name is None and '#' in app_config:  # pragma: nocover
        app_config, app_name = app_config.split('#', 1)
    if not os.path.isfile(app_config):  # pragma: nocover
        parser.error('Can\'t find config file: %s' % app_config)

    config = appconfig(
        'config:' + options.app_config,
        name=app_name, relative_to=os.getcwd()).local_conf

    db_url = config['sqlalchemy.url']
    package_name = config['project']
    c2cgeoportal.schema = config['schema']

    repository = pkg_resources.resource_filename(
        package_name, 'CONST_migration')
    migrate_main(argv=args, url=db_url, repository=repository)
