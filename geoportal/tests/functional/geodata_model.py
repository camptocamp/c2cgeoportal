import typing

import sqlalchemy.ext.declarative
from geoalchemy2 import Geometry
from sqlalchemy import Column, types

Base: typing.Any = sqlalchemy.ext.declarative.declarative_base()


class PointTest(Base):  # type: ignore[m]
    __tablename__ = "testpoint"
    __table_args__ = {"schema": "geodata"}
    id = Column(types.Integer, primary_key=True)
    geom = Column(Geometry("POINT", srid=21781))
    name = Column(types.Unicode)
    city = Column(types.Unicode)
    country = Column(types.Unicode)
