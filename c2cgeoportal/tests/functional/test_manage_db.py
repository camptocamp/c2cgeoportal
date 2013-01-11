# -*- coding: utf-8 -*-
from unittest import TestCase
import logging
from nose.plugins.attrib import attr

from pyramid import testing

log = logging.getLogger(__name__)


@attr(functional=True)
class TestCreateDB(TestCase):

    def setUp(self):
        from c2cgeoportal.scripts.manage_db import main as manage_db

        try:
            sys.argv = ['manage_db', 
                '--app-config', 'c2cgeoportal/tests/testegg/production.ini',
                'drop_version_control']
            manage_db()  # pragma: nocover
        except:
            pass

    def assert_result_equals(self, content, value):
        content = unicode(content.decode('utf-8')).split('\n')
        value = value.split('\n')
        for n, test in enumerate(zip(content, value)):
            if test[0] != 'PASS...':
                try:
                    self.assertEquals(test[0].strip(), test[1].strip())
                except AssertionError as e: # pragma: no cover
                    for i in range(max(0, n - 5), min(len(content), n + 6)):
                        if i == n:
                            log.info("> %i %s" % (i, content[i]))
                        else:
                            log.info(" %i %s" % (i, content[i]))
                    raise e

    def test_manage_db(self):
        import sys
        from cStringIO import StringIO
        from c2cgeoportal.scripts.manage_db import main as manage_db

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        sys.stdout = sys.stderr = myout = StringIO()
        sys.argv = ['manage_db']
        manage_db()
        self.assert_result_equals(myout.getvalue(), """
This script is a wrapper to the sqlalchemy-migrate migrate script.

This script passes the path to the c2cgeoportal migrate repository to the
underlying migrate command.

Usage: manage_db COMMAND ...

    Available commands:
        compare_model_to_db          - compare MetaData against the current database state
        create                       - create an empty repository at the specified path
        create_model                 - dump the current database as a Python model to stdout
        db_version                   - show the current version of the repository under version control
        downgrade                    - downgrade a database to an earlier version
        drop_version_control         - removes version control from a database
        help                         - displays help on a given command
        make_update_script_for_model - create a script changing the old MetaData to the new (current) MetaData
        manage                       - creates a Python script that runs Migrate with a set of default values
        script                       - create an empty change Python script
        script_sql                   - create empty change SQL scripts for given database
        source                       - display the Python code for a particular version in this repository
        test                         - performs the upgrade and downgrade command on the given database
        update_db_from_model         - modify the database to match the structure of the current MetaData
        upgrade                      - upgrade a database to a later version
        version                      - display the latest version available in a repository
        version_control              - mark a database as under this repository's version control

    Enter "manage_db help COMMAND" for information on a particular command.
    

Options:
  -h, --help            show this help message and exit
  -d, --debug           Shortcut to turn on DEBUG mode for logging
  -q, --disable_logging
                        Use this option to disable logging configuration

Usage: The wrapper adds two options to define the target WSGI application.

Options:
  -c APP_CONFIG, --app-config=APP_CONFIG
                        The application .ini config file (optional, default is
                        production.ini)
  -n APP_NAME, --app-name=APP_NAME
                        The application name (optional, default is "app")""")

        sys.argv = ['manage_db', 
            '--app-config', 'c2cgeoportal/tests/testegg/production.ini',
            'version_control', '0']
        manage_db()

        sys.stdout = sys.stderr = myout = StringIO()
        sys.argv = ['manage_db', 
            '--app-config', 'c2cgeoportal/tests/testegg/production.ini',
            'db_version']
        manage_db()
        self.assertEquals(myout.getvalue().strip(), "0")

        sys.argv = ['manage_db', 
            '--app-config', 'c2cgeoportal/tests/testegg/production.ini',
            'drop_version_control']
        manage_db()

        sys.stdout = old_stdout
        sys.stderr = old_stderr
