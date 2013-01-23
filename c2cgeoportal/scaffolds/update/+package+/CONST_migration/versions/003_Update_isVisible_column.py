from sqlalchemy import MetaData, Table

from c2cgeoportal import schema

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    layer = Table('layer', meta, schema=schema, autoload=True)
    conn = migrate_engine.connect()
    conn.execute(layer.update().values(isVisible = True))

def downgrade(migrate_engine):
    pass
