# -*- coding: utf-8 -*-

"""Pyramid application test package
"""

import os
from ConfigParser import ConfigParser

from paste.deploy import appconfig

mapserv_url = None
db_url = None

curdir = os.path.dirname(os.path.abspath(__file__))
configfile = os.path.realpath(os.path.join(curdir, 'test.ini'))

if os.path.exists(configfile):
    cfg = ConfigParser()
    cfg.read(configfile)
    db_url = cfg.get('test', 'sqlalchemy.url')
    mapserv_url = cfg.get('test', 'mapserv.url')


def setUpModule():
    import c2cgeoportal
    c2cgeoportal.schema = 'main'
    c2cgeoportal.srid = 21781

    # if test.in does not exist (because the z3c.recipe.filetemplate
    # part hasn't been executed) then db_url is None
    if db_url is None:
        return

    # verify that we have a working database connection before going
    # forward
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    engine = create_engine(db_url)
    try:
        engine.connect()
    except OperationalError:
        return

    import sqlahelper
    sqlahelper.add_engine(engine)

    from c2cgeoportal.models import Base
    Base.metadata.create_all()


def tearDownModule():

    # if test.in does not exist (because the z3c.recipe.filetemplate
    # part hasn't been executed) then db_url is None
    if db_url is None:
        return

    # verify that we have a working database connection before going
    # forward
    from sqlalchemy import create_engine
    from sqlalchemy.exc import OperationalError
    engine = create_engine(db_url)
    try:
        engine.connect()
    except OperationalError:
        return

    from c2cgeoportal.models import Base
    Base.metadata.drop_all(checkfirst=True)

    import sqlahelper
    sqlahelper.reset()
