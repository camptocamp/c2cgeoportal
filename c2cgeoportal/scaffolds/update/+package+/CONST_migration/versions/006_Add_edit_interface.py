from sqlalchemy import MetaData, Table, Column, types

from c2cgeoportal import schema

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    layer = Table('layer', meta, schema=schema, autoload=True)
    Column('geoTable', types.Unicode, default=u'').create(layer)

    restrictionarea = Table('restrictionarea', meta, schema=schema, autoload=True)
    Column('readwrite', types.Boolean, default=False).create(restrictionarea)

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    layer = Table('layer', meta, schema=schema, autoload=True)
    layer.c.geoTable.drop()

    restrictionarea = Table('restrictionarea', meta, schema=schema, autoload=True)
    restrictionarea.c.readwrite.drop()
