# -*- coding: utf-8 -*-

from migrate.versioning.shell import main
from pyramid.paster import get_app
from ConfigParser import ConfigParser
import warnings

def run():
    # Ignores pyramid deprecation warnings
    warnings.simplefilter('ignore', DeprecationWarning) 

    config = ConfigParser()
    config.read("CONST_production.ini")
    app = get_app("CONST_production.ini", config.get("app:c2cgeoportal", "project"))

    db = app.registry.settings['sqlalchemy.url']
    main(url=db, debug='False', repository='c2cgeoportal/c2cgeoportal/migration')
