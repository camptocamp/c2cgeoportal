from sqlalchemy import MetaData, Table, Column, types, ForeignKey

from c2cgeoportal import schema


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tsearch_table = Table('tsearch', meta, schema=schema, autoload=True)
    Column('public', types.Boolean,
           server_default='true').create(tsearch_table)
    role_table = Table('role', meta, schema=schema, autoload=True)
    Column('role_id', types.Integer, ForeignKey(role_table.c.id),
           nullable=True).create(tsearch_table)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    tsearch_table = Table('tsearch', meta, schema=schema, autoload=True)
    tsearch_table.c.public.drop()
    tsearch_table.c.role_id.drop()
