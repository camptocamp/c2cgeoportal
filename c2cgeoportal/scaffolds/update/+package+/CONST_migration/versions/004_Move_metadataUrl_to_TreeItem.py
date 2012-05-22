from sqlalchemy import MetaData, Table, Column, types
from sqlalchemy.sql import select

from c2cgeoportal import schema

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    layer = Table('layer', meta, schema=schema, autoload=True)
    treeitem = Table('treeitem', meta, schema=schema, autoload=True)
    Column('metadataURL', types.Unicode).create(treeitem)

    conn = migrate_engine.connect()
    conn.execute(treeitem.update().values(
            metadataURL=select(
                [layer.c.metadataURL],
                layer.c.id==treeitem.c.id).limit(1)))

    layer.c.metadataURL.drop()

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    treeitem = Table('treeitem', meta, schema=schema, autoload=True)
    layer = Table('layer', meta, schema=schema, autoload=True)
    Column('metadataURL', types.Unicode).create(layer)

    conn = migrate_engine.connect()
    conn.execute(layer.update().values(
            metadataURL=select(
                [treeitem.c.metadataURL],
                treeitem.c.id==layer.c.id).limit(1)))

    treeitem.c.metadataURL.drop()
