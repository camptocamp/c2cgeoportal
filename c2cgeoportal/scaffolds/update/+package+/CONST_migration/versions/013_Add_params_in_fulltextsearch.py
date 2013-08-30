from sqlalchemy import MetaData, Table, Column
from c2cgeoportal.lib.sqlalchemy_ import JSONEncodedDict

from c2cgeoportal import schema


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('tsearch', meta, schema=schema, autoload=True)
    Column('params', JSONEncodedDict, nullable=True).create(table)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('tsearch', meta, schema=schema, autoload=True)
    table.c.params.drop()
