# -*- coding: utf-8 -*-
import logging
try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1

import sqlahelper
from papyrus.geo_interface import GeoInterface
from sqlalchemy import ForeignKey, types, Table, Integer
from sqlalchemy.orm import relationship, backref
from geoalchemy import GeometryColumn, Geometry, Polygon, GeometryDDL
from formalchemy import Column
from pyramid.security import Allow, Authenticated, ALL_PERMISSIONS, DENY_ALL
from pyramid.i18n import TranslationStringFactory

from c2cgeoportal import schema, parentschema, srid

__all__ = ['Base', 'DBSession', 'Functionality', 'User', 'Role', 'TreeItem',
'TreeGroup', 'LayerGroup', 'Theme', 'Layer', 'RestrictionArea']

_ = TranslationStringFactory('c2cgeoportal')
log = logging.getLogger(__name__)

Base = sqlahelper.get_base()
DBSession = sqlahelper.get_session()

if schema is not None:
    _schema = schema
else:    
    raise Exception('schema not specified, you need to add it to your buildout config')
_parentschema = parentschema

if srid is not None:
    _srid = srid
else:
    raise Exception('srid not specified, you need to add it to your buildout config')

class FullTextSearch(GeoInterface, Base):
    __tablename__ = 'tsearch'
    __table_args__ = {'schema': _schema}
    __acl__ = [DENY_ALL]
    id = Column('id', types.Integer, primary_key=True)
    label = Column('label', types.Unicode)
    layer_name = Column('layer_name', types.Unicode)
    the_geom = GeometryColumn(Geometry(srid=_srid))
GeometryDDL(FullTextSearch.__table__)

class Functionality(Base):
    __label__ = _(u'functionality')
    __plural__ = _(u'functionalitys')
    __tablename__ = 'functionality'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]
    id = Column(types.Integer, primary_key=True)
    name = Column(types.Unicode, nullable=False, label=_(u'Name'))
    value = Column(types.Unicode, nullable=False, label=_(u'Value'))
    description = Column(types.Unicode)

    def __init__(self, name=u'', value=u'', description=u''):
        self.name = name
        self.value = value
        self.description = description

    def __unicode__ (self):
        return "%s - %s" % (self.name or u'', self.value or u'')

# association table user <> functionality
user_functionality = Table('user_functionality', Base.metadata,
     Column('user_id', Integer, ForeignKey(_schema + '.user.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     Column('functionality_id', Integer, 
            ForeignKey(_schema + '.functionality.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     schema=_schema
)

# association table role <> functionality
role_functionality = Table('role_functionality', Base.metadata,
     Column('role_id', Integer, ForeignKey(_schema + '.role.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     Column('functionality_id', Integer, 
            ForeignKey(_schema + '.functionality.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     schema=_schema
)

class User(Base):
    __label__ = _(u'user')
    __plural__ = _(u'users')
    __tablename__ = 'user'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]
    itemType = Column('type', types.String(10), nullable=False)
    __mapper_args__ = {
        'polymorphic_on': itemType,
        'polymorphic_identity': 'user',
    }
    id = Column(types.Integer, primary_key=True)
    username = Column(types.Unicode, unique=True, nullable=False, 
            label=_(u'Username'))
    _password = Column('password', types.Unicode, nullable=False,
            label=_(u'Password'))
    email = Column(types.Unicode, nullable=False, label=_(u'E-mail'))

    # functionality
    functionalities = relationship('Functionality', 
            secondary=user_functionality, cascade='all')

    # role relationship
    role_id = Column(Integer, ForeignKey(_schema + '.role.id'), nullable=False)
    role = relationship("Role", backref=backref('users', enable_typechecks=False))
    
    if _parentschema is not None and _parentschema != '':
        # parent role relationship
        parent_role_id = Column(Integer, ForeignKey(_parentschema + '.role.id'))
        parent_role = relationship("ParentRole", backref=backref('parentusers'))

    def __init__(self, username=u'', password=u'', email=u'', 
            functionalities=[], role=None):
        self.username = username
        self.password = password
        self.email = email
        self.functionalities = functionalities
        self.role = role

    def _get_password(self):
        """returns password"""
        return self._password

    def _set_password(self, password):
        """encrypts password on the fly."""
        self._password = self.__encrypt_password(password)

    def __encrypt_password(self, password):
        """Hash the given password with SHA1."""
        return unicode(sha1(password).hexdigest())

    def validate_password(self, passwd):
        """Check the password against existing credentials.
        this method _MUST_ return a boolean.

        @param passwd: the password that was provided by the user to
        try and authenticate. This is the clear text version that we will
        need to match against the (possibly) encrypted one in the database.
        @type password: string
        """
        return self._password == self.__encrypt_password(passwd)

    password = property(_get_password, _set_password)

    def __unicode__ (self):
        return self.username or u''

class Role(Base):
    __label__ = _(u'role')
    __plural__ = _(u'roles')
    __tablename__ = 'role'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]
    id = Column(types.Integer, primary_key=True)
    name = Column(types.Unicode, unique=True, nullable=False, label=_(u'Name'))
    description = Column(types.Unicode, label=_(u'Description'))
    extent = GeometryColumn(Polygon(srid=_srid))
    #product = Column(types.Unicode)

    # functionality
    functionalities = relationship('Functionality', 
            secondary=role_functionality, cascade='all')

    def __init__(self, name=u'', description=u'', functionalities=[], extent=None):
        self.name = name
        self.functionalities = functionalities
        self.extent = extent
        self.description = description

    def __unicode__ (self):
        return self.name or u''

    def _jsExtent(self):
        coords = self.extent.coords(DBSession)
        left = coords[0][0][0]
        right = coords[0][0][0]
        top = coords[0][0][1]
        bottom = coords[0][0][1]
        for way in coords:
            for coord in way:
                left = min(left, coord[0])
                right = max(right, coord[0])
                bottom = min(bottom, coord[1])
                top = max(top, coord[1])
        return "[%i, %i, %i, %i]"%(left, bottom, right, top)

    jsextent = property(_jsExtent)

GeometryDDL(Role.__table__)

class TreeItem(Base):
    __tablename__ = 'treeitem'
    __table_args__ = {'schema': _schema}
    __acl__ = [DENY_ALL]
    itemType = Column('type', types.String(10), nullable=False)
    __mapper_args__ = {'polymorphic_on': itemType}
    id = Column(types.Integer, primary_key=True)
    name = Column(types.Unicode, label=_(u'Name'))
    order = Column(types.Integer, nullable=False, label=_(u'Order'))
    metadataURL = Column(types.Unicode, label=_(u'Metadata URL'))

    def __init__(self, name=u'', order=0):
        self.name = name
        self.order = order

    def __unicode__ (self):
        return self.name or u''

# association table LayerGroup <> TreeItem
layergroup_treeitem = Table('layergroup_treeitem', Base.metadata,
     Column('treegroup_id', Integer, ForeignKey(_schema + '.treegroup.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     Column('treeitem_id', Integer, ForeignKey(_schema + '.treeitem.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     schema=_schema
)

class TreeGroup(TreeItem):
    __tablename__ = 'treegroup'
    __table_args__ = {'schema': _schema}
    __acl__ = [DENY_ALL]
    __mapper_args__ = {'polymorphic_identity': 'treegroup'}
    id = Column(types.Integer, ForeignKey(_schema + '.treeitem.id'), 
            primary_key=True)

    # relationship with Role and Layer
    children = relationship('TreeItem', backref='parents', 
            secondary=layergroup_treeitem, cascade='all')

    def __init__(self, name=u'', order=u''):
        TreeItem.__init__(self, name=name, order=order) 

class LayerGroup(TreeGroup):
    __label__ = _(u'layergroup')
    __plural__ = _(u'layergroups')
    __tablename__ = 'layergroup'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'group'}
    id = Column(types.Integer, ForeignKey(_schema + '.treegroup.id'), 
            primary_key=True)
    isExpanded = Column(types.Boolean, label=_(u'Expanded'))
    isInternalWMS = Column(types.Boolean, label=_(u'Internal WMS'))
    # children have radio button instance of check box
    isBaseLayer = Column(types.Boolean, label=_(u'Group of base layers')) 

    def __init__(self, name=u'', order=u'', isExpanded=False, 
            isInternalWMS=True, isBaseLayer=False):
        TreeGroup.__init__(self, name=name, order=order) 
        self.isExpanded = isExpanded
        self.isInternalWMS = isInternalWMS
        self.isBaseLayer = isBaseLayer

class Theme(TreeGroup):
    __label__ = _(u'theme')
    __plural__ = _(u'themes')
    __tablename__ = 'theme'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'theme'}
    id = Column(types.Integer, ForeignKey(_schema + '.treegroup.id'), 
            primary_key=True)
    icon = Column(types.Unicode, label=_(u'Icon'))
    display = Column(types.Boolean, label=_(u'Display')) # display in theme selector

    def __init__(self, name=u'', order=100, icon=u'', display=True):
        TreeGroup.__init__(self, name=name, order=order) 
        self.icon = icon
        self.display = display

class Layer(TreeItem):
    __label__ = _(u'layer')
    __plural__ = _(u'layers')
    __tablename__ = 'layer'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'layer'}
    id = Column(types.Integer, ForeignKey(_schema + '.treeitem.id'), 
            primary_key=True)

    public = Column(types.Boolean, default=True, label=_(u'Public'))
    isVisible = Column(types.Boolean, default=True, label=_(u'Visible')) # by default
    isChecked = Column(types.Boolean, default=True, label=_(u'Checked')) # by default
    icon = Column(types.Unicode, label=_(u'Icon')) # on the tree
    layerType = Column(types.Enum("internal WMS", "external WMS", 
            "internal WMTS", "external WMTS", "empty", 
            name=_schema+".layerType"), label=_(u'Type'))
    url = Column(types.Unicode, label=_(u'Base URL')) # for externals
    serverResolutions = Column(types.Unicode, label=_(u'Server Resolutions')) # for external WMTS
    maxExtent = Column(types.Unicode, label=_(u'Max Extent')) # for external WMTS
    imageType = Column(types.Enum("image/jpeg", "image/png", 
            name=_schema+".imageType"), label=_(u'Image type'))
    kml = Column(types.Unicode, label=_(u'KML 3D')) # for kml 3D
    isSingleTile = Column(types.Boolean, label=_(u'Single tile')) # for extenal WMS
    no2D = Column(types.Boolean, label=_(u'No 2D')) # only kml 3D
    legend = Column(types.Boolean, default=True, label=_(u'Display legend')) # on the tree
    legendImage = Column(types.Unicode, label=_(u'Legend Image')) # fixed legend image
    legendRule = Column(types.Unicode, label=_(u'Legend Rule')) # on wms legend only one rule
    minResolution = Column(types.Float, label=_(u'Min resolution')) # for all except internal WMS
    maxResolution = Column(types.Float, label=_(u'Max resolution')) # for all except internal WMS
    disclaimer = Column(types.Unicode, label=_(u'Disclaimer'))

    def __init__(self, name=u'', order=0, public=True, icon=u'', 
            layerType=u'internal WMS'):
        TreeItem.__init__(self, name=name, order=order) 
        self.public = public
        self.icon = icon
        self.layerType = layerType

# association table role <> restriciton area
role_ra = Table('role_restrictionarea', Base.metadata,
     Column('role_id', Integer, ForeignKey(_schema + '.role.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     Column('restrictionarea_id', Integer, 
            ForeignKey(_schema + '.restrictionarea.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     schema=_schema
)

# association table layer <> restriciton area
layer_ra = Table('layer_restrictionarea', Base.metadata,
     Column('layer_id', Integer, ForeignKey(_schema + '.layer.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     Column('restrictionarea_id', Integer, 
            ForeignKey(_schema + '.restrictionarea.id', 
            onupdate="CASCADE", ondelete="CASCADE"), primary_key=True),
     schema=_schema
)

class RestrictionArea(Base):
    __label__ = _(u'restrictionarea')
    __plural__ = _(u'restrictionareas')
    __tablename__ = 'restrictionarea'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, Authenticated, ALL_PERMISSIONS),
    ]

    id = Column(types.Integer, primary_key=True)
    area = GeometryColumn(Polygon(srid=_srid))
    name = Column(types.Unicode, label=_(u'Name'))
    description = Column(types.Unicode, label=_(u'Description'))

    # relationship with Role and Layer
    roles = relationship('Role', secondary=role_ra, 
            backref='restrictionareas', cascade='all')
    layers = relationship('Layer', secondary=layer_ra, 
            backref='restrictionareas', cascade='all')

    def __init__(self, name='', description='', layers=[], roles=[], area=None):
        self.name = name
        self.description = description
        self.layers = layers
        self.roles = roles
        self.area = area

    def __unicode__ (self):
        return self.name or u''

GeometryDDL(RestrictionArea.__table__)

if _parentschema is not None and _parentschema != '':
    class ParentRole(Base):
        __label__ = _(u'parentrole')
        __plural__ = _(u'parentroles')
        __tablename__ = 'role'
        __table_args__ = {'schema': _parentschema}
        __acl__ = [
            (Allow, Authenticated, ('view')),
        ]
        id = Column(types.Integer, primary_key=True)
        name = Column(types.Unicode, unique=True, nullable=False, label=_(u'Name'))

        def __init__(self, name=u''):
            self.name = name

        def __unicode__ (self):
            return self.name or u''
