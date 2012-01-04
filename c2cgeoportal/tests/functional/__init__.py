# -*- coding: utf-8 -*-

"""Pyramid application test package
"""

import os
from ConfigParser import ConfigParser

from paste.deploy import appconfig

# set by the nose plugin
db_url = None
mapserv_url = None

def setUpModule():
    import c2cgeoportal
    c2cgeoportal.schema = 'main'
    c2cgeoportal.srid = 21781

    if db_url is None:
        return

    import sqlahelper
    from sqlalchemy import create_engine
    sqlahelper.add_engine(create_engine(db_url))

    from c2cgeoportal.models import Base
    Base.metadata.create_all()

def tearDownModule():
    if db_url is None:
        return

    from c2cgeoportal.models import Base
    Base.metadata.drop_all(checkfirst=True)

    import sqlahelper
    sqlahelper.reset()
