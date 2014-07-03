from sqlalchemy import MetaData, Table, Column, types, ForeignKey
from migrate import *

from c2cgeoportal import schema


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    theme_table = Table('theme', meta, schema=schema, autoload=True)
    functionality_table = Table('functionality', meta, schema=schema,
        autoload=True)
    theme_functionality = Table(
        'theme_functionality', meta,
        Column('theme_id', types.Integer,
            ForeignKey(theme_table.c.id), primary_key=True),
        Column('functionality_id', types.Integer,
            ForeignKey(functionality_table.c.id), primary_key=True),
        schema=schema,
    )
    theme_functionality.create()


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('theme_functionality', meta, schema=schema, autoload=True)
    table.drop()
