import logging
import os

from nose.plugins import Plugin

from c2cgeoportal.tests import functional

log = logging.getLogger('nose.plugins.c2cgeoportal')

class c2cgeoportal(Plugin):
    """A nose plugin that adds c2cgeoportal-specific command line options,
namely --db-url (SQLAlchemy database URL) and --mapserv-url (URL to the
mapserv service).
    """

    name = 'c2cgeoportal'

    def options(self, parser, env=os.environ):
        super(c2cgeoportal, self).options(parser, env=env)
        opt = parser.add_option
        opt('--db-url', action='store', dest='db_url',
            help='SQLAlchemy database URL')
        opt('--mapserv-url', action='store', dest='mapserv_url',
            default='http://localhost/cgi-bin/mapserv',
            help='MapServer URL')

    def configure(self, options, conf):
        super(c2cgeoportal, self).configure(options, conf)
        if not self.enabled:
            return
        functional.db_url = options.db_url
        functional.mapserv_url = options.mapserv_url
