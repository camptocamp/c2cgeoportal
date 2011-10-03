# -*- coding: utf-8 -*-
from migrate.versioning.shell import main
from pyramid.paster import get_app

def run():
    app = get_app("c2cgeoportal/production.ini", "project")
    db = app.registry.settings['sqlalchemy.url']

    main(url=db, debug='False', repository='c2cgeoportal/c2cgeoportal/migration')
