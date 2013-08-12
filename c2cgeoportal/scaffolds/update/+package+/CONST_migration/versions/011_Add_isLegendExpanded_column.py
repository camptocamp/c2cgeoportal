from sqlalchemy import MetaData, Table, Column, types

from c2cgeoportal import schema

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('layer', meta, schema=schema, autoload=True)
    Column('isLegendExpanded', types.Boolean, default=False).create(table)

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('layer', meta, schema=schema, autoload=True)
    table.c.isLegendExpanded.drop()

