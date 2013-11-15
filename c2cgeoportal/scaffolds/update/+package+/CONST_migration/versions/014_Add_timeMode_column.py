from sqlalchemy import MetaData, Table, Column, types

from c2cgeoportal import schema


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    layer = Table('layer', meta, schema=schema, autoload=True)
    c = Column('timeMode', types.Enum(
        'disabled',
        'single',
        'range',
        native_enum=False), default='disabled')
    c.create(layer, populate_default=True)
    c.alter(nullable=False)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    layer = Table('layer', meta, schema=schema, autoload=True)
    layer.c.timeMode.drop()

