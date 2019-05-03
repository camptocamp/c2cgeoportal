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

And in the file ``<package>/forms.py``::

    # Add a field set (form) for the title
    Title = FieldSet(models.Title)

    # Add a field set for the user details
    UserDetail = FieldSet(models.UserDetail)
    # Need to hide the password
    password = forms.DblPasswordField(UserDetail, UserDetail._password)
    UserDetail.append(password)
    # Fix the fields order
    fieldOrder = [UserDetail.username.validate(forms.unique_validator)
                                   .with_metadata(mandatory=''),
                  password, UserDetail.role]
    if hasattr(UserDetail, 'parent_role'):
        fieldOrder.append(UserDetail.parent_role)
    fieldOrder.extend([UserDetail.title,
            UserDetail.functionalities.
                    set(renderer=forms.FunctionalityCheckBoxTreeSet)])
    UserDetail.configure(include=fieldOrder)

    # Add a grid for the title
    TitleGrid = Grid(models.Title)

    # Add a grid for the  user details
    UserGrid = Grid(models.UserDetail)
    # Visible fields
    fieldOrder = [UserDetail.username,
                  UserDetail.title,
                  UserDetail.functionalities,
                  UserDetail.role]
    if hasattr(UserGrid, 'parent_role'):
        fieldOrder.append(UserDetail.parent_role)
    UserGrid.configure(include=fieldOrder)

We can change the renderer of a field, for example change the
Role renderer::

    Role.name.set(renderer=AnOtherRenderer, ...)

And if we need an other resource (javascript or stylesheet)::

    from fa.jquery import fanstatic_resources
    from fanstatic import Resource, Group, Library
    from pyramid_formalchemy import events as fa_events

    fanstatic_lib = Library('<package>_admin', 'static')
    new_js = Resource(fanstatic_lib, '<path_to_javascript.js>',
        depends=[fanstatic_resources.<depends_on>])
    new_css = Resource(fanstatic_lib, '<path_to_stylesheet.css>')

    @fa_events.subscriber([models.Role, fa_events.IBeforeRenderEvent])
    def before_render_role(context, event):
        Group([new_js, new_css]).need()

And in the ``setup.py`` we need to add in the ``entry_points``::

    'fanstatic.libraries': [
        '<package>_admin = <package>.forms:fanstatic_lib',
    ],
