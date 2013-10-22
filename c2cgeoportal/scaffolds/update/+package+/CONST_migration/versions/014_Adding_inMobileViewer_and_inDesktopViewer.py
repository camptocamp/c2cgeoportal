from sqlalchemy import MetaData, Table, Column, types
from migrate import *

from c2cgeoportal import schema

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    conn = migrate_engine.connect()

    theme = Table('theme', meta, schema=schema, autoload=True)
    Column('inMobileViewer', types.Boolean, default=False).create(theme)
    Column('inDesktopViewer', types.Boolean, default=True).create(theme)
    conn.execute(theme.update().values(inDesktopViewer=theme.c.display))
    theme.c.display.drop()

    layer = Table('layer', meta, schema=schema, autoload=True)
    Column('inMobileViewer', types.Boolean, default=True).create(layer)
    Column('inDesktopViewer', types.Boolean, default=True).create(layer)
    conn.execute(layer.update().values(inDesktopViewer=layer.c.isVisible))
    layer.c.isVisible.drop()

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    conn = migrate_engine.connect()

    theme = Table('theme', meta, schema=schema, autoload=True)
    Column('display', types.Boolean, default=True).create(theme)
    conn.execute(theme.update().values(display=theme.c.inDesktopViewer))
    theme.c.inMobileViewer.drop()
    theme.c.inDesktopViewer.drop()

    layer = Table('layer', meta, schema=schema, autoload=True)
    Column('isVisible', types.Boolean, default=True).create(layer)
    conn.execute(layer.update().values(isVisible=layer.c.inDesktopViewer))
    layer.c.inMobileViewer.drop()
    layer.c.inDesktopViewer.drop()
