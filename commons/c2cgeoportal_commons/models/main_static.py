class Shorturl(Base):
    __tablename__ = "shorturl"
    __table_args__ = {"schema": _schema + "_static"}
    __acl__ = [DENY_ALL]
    id = Column(Integer, primary_key=True)
    url = Column(Unicode)
    ref = Column(String(20), index=True, unique=True, nullable=False)
    creator_email = Column(Unicode(200))
    creation = Column(DateTime)
    last_hit = Column(DateTime)
    nb_hits = Column(Integer)
