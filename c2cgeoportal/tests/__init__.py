# -*- coding: utf-8 -*-

"""Pyramid application test package
"""

import os
from ConfigParser import ConfigParser

from paste.deploy import appconfig
import sqlahelper
from sqlalchemy import create_engine

curdir = os.path.dirname(os.path.abspath(__file__))
configfile = os.path.realpath(os.path.join(curdir, 'test.ini'))

cfg = ConfigParser()
cfg.read(configfile)
sqlalchemy_url = cfg.get('test', 'sqlalchemy.url')
mapserv_url = cfg.get('test', 'mapserv.url')
sqlahelper.add_engine(create_engine(sqlalchemy_url))

def setUpModule():
    import c2cgeoportal
    c2cgeoportal.schema = 'main'
    c2cgeoportal.srid = 21781

    from c2cgeoportal.models import Base
    Base.metadata.create_all()

def tearDownModule():
    from c2cgeoportal.models import Base
    Base.metadata.drop_all(checkfirst=True)
