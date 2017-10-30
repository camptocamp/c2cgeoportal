.. _integrator_extend_data_model:

Extend the data model
=====================

The Data model can be extended in the file ``<package>/models.py``
and the corresponding admin interface configuration
in the file ``<package>/forms.py``.

For example to add some user details, including a link to a
new class named "Title", add to ``<package>/models.py``::

    # Used to hide the original user in the admin interface
    User.__acl__ = [DENY_ALL]

    class UserDetail(User):
        __label__ = _('userdetail')
        __plural__ = _('userdetails')
        __tablename__ = 'userdetail'
        __table_args__ = {'schema': _schema}
        __acl__ = [
            (Allow, Authenticated, ALL_PERMISSIONS),
        ]
        __mapper_args__ = {'polymorphic_identity': 'detailed'}
        id = Column(types.Integer, ForeignKey(_schema + '.user.id'),
                primary_key=True)

        phone = Column(types.Unicode, nullable=False, label=_(u'phone'))

        # title
        title_id = Column(Integer, ForeignKey(_schema + '.title.id'), nullable=False)
        title = relationship("Title", backref=backref('users'))

        def __init__(self, username=u'', password=u'', functionalities=[],
                     phone=u'', email=u'', title=None, role=None):
            User.__init__(self, username, password, email, functionalities, role)
            self.phone = phone
            self.title = title

    class Title(Base):
        __label__ = _('title')
        __plural__ = _('titles')
        __tablename__ = 'title'
        __table_args__ = {'schema': _schema}
        __acl__ = [
            (Allow, Authenticated, ALL_PERMISSIONS),
        ]
        id = Column(types.Integer, primary_key=True)
        name = Column(types.Unicode, nullable=False, label=_(u'Name'))
        description = Column(types.Unicode, label=_(u'Description'))

        def __init__(self, name=u'', description=u''):
            self.name = name
            self.description = description

        def __unicode__ (self):
            return self.name or u''
