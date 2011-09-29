"""Create the application's database.
"""

import sys
from pyramid.paster import get_app

from c2cgeoportail import schema
from c2cgeoportail import parentschema

import transaction

def main():
    if len(sys.argv) < 2:
        sys.exit("""Usage: buildout/bin/create_db INI_FILE OPTION..."

Available options:
  -d  --drop        drop the curent tables
  -p  --populate    populate the table with example data""")

    # read the configuration
    ini_file = sys.argv[1]
    app = get_app(ini_file, "c2cgeoportail")
    settings = app.registry.settings

    # sets the schema and load the database model
    schema = settings['schema']
    parentschema = settings['parentschema']
    from project import models
    from c2cgeoportail import models as c2cmodels

    if "-d" in sys.argv[2:] or '--drop' in sys.argv[2:]:
        print "Dropping tables"
        c2cmodels.Base.metadata.drop_all()

    print "Creating tables"
    c2cmodels.Base.metadata.create_all()
    sess = c2cmodels.DBSession()

    admin = models.User(username=u'admin', 
                password=u'admin',
                )
    roleadmin = c2cmodels.Role(name=u'role_admin') 
    admin.role = roleadmin
    sess.add_all([admin, roleadmin])

    if "-p" in sys.argv[2:] or '--populate' in sys.argv[2:]:
        print "Populate the Database"

        # add the objects creation there

        sess.add_all([]) # add the oblect that we want to commit in the array

    transaction.commit()
    print "Commited successfully"

