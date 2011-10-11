# -*- coding: utf-8 -*-
"""Create the application's database.

Run this once after installing the application::

    python -m c2cgeoportal.scripts.create_db development.ini [-d|--drop]
"""
import logging.config
import sys

from pyramid.paster import get_app
import transaction

from c2cgeoportal import schema
from c2cgeoportal import parentschema

def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python -m c2cgeoportal.scripts.create_db " \
                 "INI_FILE [-d|--drop]")
    ini_file = sys.argv[1]
    logging.config.fileConfig(ini_file)
    log = logging.getLogger(__name__)

    app = get_app(ini_file, "c2cgeoportal")
    settings = app.registry.settings

    schema = settings['schema']
    parentschema = settings['parentschema']
    import c2cgeoportal.models

    if len(sys.argv) > 2 and sys.argv[2] in ['-d', '--drop']:
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
