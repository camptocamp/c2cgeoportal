# -*- coding: utf-8 -*-
"""Create the application's database.

Run this once after installing the application::

    python -m c2cgeoportal.scripts.create_db development.ini [-d|--drop]
"""

import logging
from optparse import OptionParser

from pyramid.paster import get_app
import transaction


def main():
    parser = OptionParser("Create and populate the database tables.")
    parser.add_option('-i', '--iniconfig', default='CONST_production.ini', 
            help='project .ini config file')
    parser.add_option('-d', '--drop', action="store_true",  default=False, 
            help='drop the table if already exists')
    parser.add_option('-p', '--populate', action="store_true",  default=False, 
            help='populate the database')

    (options, args) = parser.parse_args()

    logging.config.fileConfig(options.iniconfig)
    log = logging.getLogger(__name__)

    config = ConfigParser()
    config.read(options.iniconfig)

    app = get_app(options.iniconfig, config.get('app:c2cgeoportal', 'project'))
    settings = app.registry.settings

    schema = settings['schema']
    parentschema = settings['parentschema']
    srid = settings['srid']
    import c2cgeoportal.models

    if options.drop:
        log.info("Dropping tables")
        models.Base.metadata.drop_all()
    # Abort if any tables exist to prevent accidental overwriting
    for table in models.Base.metadata.sorted_tables:
        log.debug("checking if table '%s' exists", table.name)
        if table.exists():
            raise RuntimeError("database table '%s' exists" % table.name)

    log.info("Creating tables")
    models.Base.metadata.create_all()
    sess = models.DBSession()

    titleadmin = models.Title(u'Administrator')
    admin = models.User(username=u'admin', 
                password=u'admin',
                title=titleadmin
                )
    roleadmin = models.Role(name=u'role_admin') 
    admin.role = roleadmin
    sess.add_all([admin, roleadmin, titleadmin])

    transaction.commit()


if __name__ == "__main__":  
    main()
