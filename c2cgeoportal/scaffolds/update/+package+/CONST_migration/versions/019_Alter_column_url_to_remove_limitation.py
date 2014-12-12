from sqlalchemy import MetaData, Table, types

from c2cgeoportal import schema

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('shorturl', meta, schema='%s_static' % schema, autoload=True)
    table.c.url.alter(type=types.Unicode)

def downgrade(migrate_engine):
    pass
