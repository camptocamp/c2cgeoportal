# -*- coding: utf-8 -*-
from migrate.versioning.shell import main
from pyramid.paster import get_app

def run():
    app = get_app("c2cgeoportail/production.ini", "c2cgeoportail")
    db = app.registry.settings['sqlalchemy.url']

    main(url=db, debug='False', repository='c2cgeoportail/c2cgeoportail/migration')
