from sqlalchemy import MetaData, Table, Column, types

from c2cgeoportal import schema

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('user', meta, schema=schema, autoload=True)
    Column('is_password_changed', types.Boolean, default=False).create(table)

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('user', meta, schema=schema, autoload=True)
    table.c.is_password_changed.drop()
