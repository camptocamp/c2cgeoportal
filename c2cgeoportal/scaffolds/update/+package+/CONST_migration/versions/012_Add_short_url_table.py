from sqlalchemy import MetaData, Table, Column, types

from c2cgeoportal import schema


def upgrade(migrate_engine):
    metadata = MetaData()
    short_url = Table(
        'shorturl', metadata,
        Column('id', types.Integer, primary_key=True),
        Column('url', types.Unicode(1000)),
        Column('ref', types.String(20), index=True, unique=True),
        Column('creator_email', types.Unicode(200)),
        Column('creation', types.DateTime),
        Column('last_hit', types.DateTime),
        Column('nb_hits', types.Integer),
        schema=schema,
    )
    short_url.create(bind=migrate_engine)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    table = Table('shorturl', meta, schema=schema, autoload=True)
    table.drop()
