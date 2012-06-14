from sqlalchemy import MetaData, Table, Column, types
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from c2cgeoportal import schema


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    layer = Table('layer', meta, schema=schema, autoload=True)
    layer.c.layerType.alter(type=types.Enum("internal WMS",
            "WMTS", "no 2D", native_enum=False))
    types.Enum("internal WMS", "external WMS", 
            "internal WMTS", "external WMTS", "empty",
            name=schema + ".layerType", metadata=meta).drop()
    layer.c.serverResolutions.drop()
    layer.c.maxExtent.drop()
    layer.c.imageType.alter(type=types.Enum("image/jpeg", "image/png",
            native_enum=False))
    types.Enum("image/jpeg", "image/png",
            name=schema + ".imageType", metadata=meta).drop()
    Column('style', types.Unicode).create(layer)
    Column('dimensions', types.Unicode).create(layer)
    Column('matrixSet', types.Unicode).create(layer)
    Column('wmsUrl', types.Unicode).create(layer)
    Column('wmsLayers', types.Unicode).create(layer)
    layer.c.no2D.drop()


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    layer = Table('layer', meta, schema=schema, autoload=True)
    layer.c.layerType.alter(name='old_layerType')
    layerType = types.Enum("internal WMS", "external WMS",
            "internal WMTS", "external WMTS", "empty",
            name=schema + ".layerType", metadata=meta)
    layerType.create()
    Column('layerType', layerType).create(layer)
    Column('serverResolutions', types.Unicode).create(layer)
    Column("maxExtent", types.Unicode).create(layer)
    layer.c.imageType.alter(name='old_imageType')
    imageType = types.Enum("image/jpeg", "image/png",
             name=schema + ".imageType", metadata=meta)
    imageType.create()
    Column('imageType', imageType).create(layer)
    layer.c.style.drop()
    layer.c.dimensions.drop()
    layer.c.matrixSet.drop()
    layer.c.wmsUrl.drop()
    layer.c.wmsLayers.drop()
    Column('no2D', types.Boolean).create(layer)


    Base = declarative_base()
    class Layer(Base):
        __tablename__ = 'layer'
        __table_args__ = {
            'schema': schema,
            'autoload_with': migrate_engine,
        }
        __autoload__ = True

    Session = sessionmaker(bind=migrate_engine)
    session = Session()
    for l in session.query(Layer).all():
        l.layerType = l.old_layerType
        l.imageType = l.old_imageType
        if l.no2D:
            l.layerType = 'no 2D'
        session.add(l)
    session.commit()

    # new metadata to reload the table columns
    meta = MetaData(bind=migrate_engine)
    layer = Table('layer', meta, schema=schema, autoload=True)
    layer.c.old_layerType.drop()
    layer.c.old_imageType.drop()
