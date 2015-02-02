# -*- coding: utf-8 -*-

# Copyright (c) 2011-2015, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import logging
try:
    from hashlib import sha1
    sha1  # suppress pyflakes warning
except ImportError:  # pragma: nocover
    from sha import new as sha1

import sqlahelper
from papyrus.geo_interface import GeoInterface
from sqlalchemy import ForeignKey, Table, event
from sqlalchemy.types import Integer, Boolean, Unicode, Float, String, \
    Enum, DateTime, UserDefinedType
from sqlalchemy.schema import Index
from sqlalchemy.orm import relationship, backref
from sqlalchemy.exc import UnboundExecutionError
from geoalchemy2 import Geometry, func
from geoalchemy2.shape import to_shape
from formalchemy import Column
from pyramid.security import Allow, ALL_PERMISSIONS, DENY_ALL
from pyramid.i18n import TranslationStringFactory

from c2cgeoportal import schema, parentschema, srid
from c2cgeoportal.lib import caching
from c2cgeoportal.lib.sqlalchemy_ import JSONEncodedDict

__all__ = [
    'Base', 'DBSession', 'Functionality', 'User', 'Role', 'TreeItem',
    'TreeGroup', 'LayerGroup', 'Theme', 'Layer', 'RestrictionArea',
    'LayerV1', 'LayerInternalWMS', 'LayerExternalWMS', 'LayerWMTS',
    'Interface', 'UIMetadata', 'WMTSDimension', 'LayergroupTreeitem'
]

_ = TranslationStringFactory('c2cgeoportal')
log = logging.getLogger(__name__)

Base = sqlahelper.get_base()
DBSession = sqlahelper.get_session()

DBSessions = {
    'dbsession': DBSession,
}

try:
    postgis_version = DBSession.execute(func.postgis_version()).scalar()
except UnboundExecutionError:  # pragma: nocover - needed by non functional tests
    postgis_version = '2.0'
management = postgis_version.startswith('1.')

AUTHORIZED_ROLE = 'role_admin'

if schema is not None:
    _schema = schema
else:  # pragma: nocover
    raise Exception(
        'schema not specified, you need to add it to your config'
    )
_parentschema = parentschema

if srid is not None:
    _srid = srid
else:  # pragma: nocover
    raise Exception(
        'srid not specified, you need to add it to your config'
    )


def cache_invalidate_cb(*args):
    caching.invalidate_region()


class TsVector(UserDefinedType):
    """ A custom type for PostgreSQL's tsvector type. """
    def get_col_spec(self):  # pragma: nocover
        return 'TSVECTOR'


class FullTextSearch(GeoInterface, Base):
    __tablename__ = 'tsearch'
    __table_args__ = (
        Index('tsearch_ts_idx', 'ts', postgresql_using='gin'),
        {'schema': _schema}
    )
    __acl__ = [DENY_ALL]

    id = Column(Integer, primary_key=True)
    label = Column(Unicode)
    layer_name = Column(Unicode)
    role_id = Column(Integer, ForeignKey(_schema + '.role.id'), nullable=True)
    role = relationship("Role")
    public = Column(Boolean, server_default='true')
    ts = Column(TsVector)
    the_geom = Column(Geometry('GEOMETRY', srid=_srid, management=management))
    params = Column(JSONEncodedDict, nullable=True)


class Functionality(Base):
    __label__ = _(u'functionality')
    __plural__ = _(u'functionalitys')
    __tablename__ = 'functionality'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False, label=_(u'Name'))
    value = Column(Unicode, nullable=False, label=_(u'Value'))
    description = Column(Unicode)

    def __init__(self, name=u'', value=u'', description=u''):
        self.name = name
        self.value = value
        self.description = description

    def __unicode__(self):
        return "%s - %s" % (self.name or u'', self.value or u'')  # pragma: nocover

# association table role <> functionality
role_functionality = Table(
    'role_functionality', Base.metadata,
    Column(
        'role_id', Integer,
        ForeignKey(_schema + '.role.id'), primary_key=True
    ),
    Column(
        'functionality_id', Integer,
        ForeignKey(_schema + '.functionality.id'), primary_key=True
    ),
    schema=_schema
)

# association table theme <> functionality
theme_functionality = Table(
    'theme_functionality', Base.metadata,
    Column(
        'theme_id', Integer,
        ForeignKey(_schema + '.theme.id'), primary_key=True
    ),
    Column(
        'functionality_id', Integer,
        ForeignKey(_schema + '.functionality.id'), primary_key=True
    ),
    schema=_schema
)


class User(Base):
    __label__ = _(u'user')
    __plural__ = _(u'users')
    __tablename__ = 'user'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    item_type = Column('type', String(10), nullable=False)
    __mapper_args__ = {
        'polymorphic_on': item_type,
        'polymorphic_identity': 'user',
    }

    id = Column(Integer, primary_key=True)
    username = Column(
        Unicode, unique=True, nullable=False,
        label=_(u'Username'))
    _password = Column(
        'password', Unicode, nullable=False,
        label=_(u'Password'))
    email = Column(Unicode, nullable=False, label=_(u'E-mail'))
    is_password_changed = Column(Boolean, default=False, label=_(u'PasswordChanged'))

    # role relationship
    role_id = Column(Integer, ForeignKey(_schema + '.role.id'), nullable=False)
    role = relationship("Role", backref=backref('users', enable_typechecks=False))

    if _parentschema is not None and _parentschema != '':  # pragma: no cover
        # parent role relationship
        parent_role_id = Column(Integer, ForeignKey(_parentschema + '.role.id'))
        parent_role = relationship("ParentRole", backref=backref('parentusers'))

    def __init__(
        self, username=u'', password=u'', email=u'', is_password_changed=False,
        functionalities=[], role=None
    ):
        self.username = username
        self.password = password
        self.email = email
        self.is_password_changed = is_password_changed
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
        return sha1(password.encode('utf8')).hexdigest()

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

    def __unicode__(self):
        return self.username or u''  # pragma: nocover


class Role(Base):
    __label__ = _(u'role')
    __plural__ = _(u'roles')
    __tablename__ = 'role'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True, nullable=False, label=_(u'Name'))
    description = Column(Unicode, label=_(u'Description'))
    extent = Column(Geometry('POLYGON', srid=_srid, management=management))

    # functionality
    functionalities = relationship(
        'Functionality', secondary=role_functionality,
        cascade='save-update,merge,refresh-expire'
    )

    def __init__(self, name=u'', description=u'', functionalities=[], extent=None):
        self.name = name
        self.functionalities = functionalities
        self.extent = extent
        self.description = description

    def __unicode__(self):
        return self.name or u''  # pragma: nocover

    @property
    def bounds(self):
        if self.extent is None:
            return None
        return to_shape(self.extent).bounds


class TreeItem(Base):
    __tablename__ = 'treeitem'
    __table_args__ = {'schema': _schema}
    __acl__ = [DENY_ALL]
    item_type = Column('type', String(10), nullable=False)
    __mapper_args__ = {'polymorphic_on': item_type}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, label=_(u'Name'))
    metadata_url = Column(Unicode, label=_(u'Metadata URL'))  # shouldn't be used in V3

    @property
    def parents(self):  # pragma: nocover
        return [c.group for c in self.parents_relation]

    def is_in_interface(self, name):
        if not hasattr(self, 'interfaces'):  # pragma: nocover
            return False

        for interface in self.interfaces:
            if interface.name == name:
                return True

        return False

    def __init__(self, name=u''):
        self.name = name

    def __unicode__(self):
        return self.name or u''  # pragma: nocover

event.listen(TreeItem, 'after_insert', cache_invalidate_cb, propagate=True)
event.listen(TreeItem, 'after_update', cache_invalidate_cb, propagate=True)
event.listen(TreeItem, 'after_delete', cache_invalidate_cb, propagate=True)


# association table LayerGroup <> TreeItem
class LayergroupTreeitem(Base):
    __tablename__ = 'layergroup_treeitem'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    # required by formalchemy
    id = Column(Integer, primary_key=True)
    treegroup_id = Column(
        Integer, ForeignKey(_schema + '.treegroup.id')
    )
    group = relationship(
        'TreeGroup',
        backref=backref(
            'children_relation',
            order_by="LayergroupTreeitem.ordering",
            cascade='save-update,merge,delete',
        ),
        primaryjoin="LayergroupTreeitem.treegroup_id==TreeGroup.id",
    )
    treeitem_id = Column(
        Integer, ForeignKey(_schema + '.treeitem.id')
    )
    item = relationship(
        'TreeItem',
        backref=backref(
            'parents_relation', cascade='save-update,merge,delete'
        ),
        primaryjoin="LayergroupTreeitem.treeitem_id==TreeItem.id",
    )
    ordering = Column(Integer)

    # Used by formalchemy
    def __unicode__(self):  # pragma: nocover
        return self.group.name

    def __init__(self, group=None, item=None, ordering=0):
        self.group = group
        self.item = item
        self.ordering = ordering

event.listen(LayergroupTreeitem, 'after_insert', cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, 'after_update', cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, 'after_delete', cache_invalidate_cb, propagate=True)


class TreeGroup(TreeItem):
    __tablename__ = 'treegroup'
    __table_args__ = {'schema': _schema}
    __acl__ = [DENY_ALL]

    id = Column(
        Integer, ForeignKey(_schema + '.treeitem.id'), primary_key=True
    )

    def _get_children(self):
        return [c.item for c in self.children_relation]

    def _set_children(self, children):
        self.children_relation = [
            LayergroupTreeitem(self, item, index) for index, item in enumerate(children)
        ]

    children = property(_get_children, _set_children)

    def __init__(self, name=u''):
        TreeItem.__init__(self, name=name)


class LayerGroup(TreeGroup):
    __label__ = _(u'layergroup')
    __plural__ = _(u'layergroups')
    __tablename__ = 'layergroup'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'group'}

    id = Column(
        Integer, ForeignKey(_schema + '.treegroup.id'), primary_key=True
    )
    is_expanded = Column(Boolean, label=_(u'Expanded'))  # shouldn't be used in V3
    is_internal_wms = Column(Boolean, label=_(u'Internal WMS'))
    # children have radio button instance of check box
    is_base_layer = Column(Boolean, label=_(u'Group of base layers'))  # Shouldn't be used in V3

    def __init__(
            self, name=u'', is_expanded=False,
            is_internal_wms=True, is_base_layer=False):
        TreeGroup.__init__(self, name=name)
        self.is_expanded = is_expanded
        self.is_internal_wms = is_internal_wms
        self.is_base_layer = is_base_layer


# role theme link for restricted theme
restricted_role_theme = Table(
    'restricted_role_theme', Base.metadata,
    Column(
        'role_id', Integer, ForeignKey(_schema + '.role.id'), primary_key=True
    ),
    Column(
        'theme_id', Integer,
        ForeignKey(_schema + '.theme.id'), primary_key=True
    ),
    schema=_schema
)


class Theme(TreeGroup):
    __label__ = _(u'theme')
    __plural__ = _(u'themes')
    __tablename__ = 'theme'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'theme'}

    id = Column(
        Integer, ForeignKey(_schema + '.treegroup.id'), primary_key=True
    )
    ordering = Column(Integer, nullable=False, label=_(u'Order'))
    public = Column(Boolean, default=True, nullable=False, label=_(u'Public'))
    icon = Column(Unicode, label=_(u'Icon'))

    # functionality
    functionalities = relationship(
        'Functionality', secondary=theme_functionality,
        cascade='save-update,merge,refresh-expire'
    )

    # restricted to role
    restricted_roles = relationship(
        'Role', secondary=restricted_role_theme,
        cascade='save-update,merge,refresh-expire',
    )

    def __init__(self, name=u'', ordering=100, icon=u''):
        TreeGroup.__init__(self, name=name)
        self.ordering = ordering
        self.icon = icon


class Layer(TreeItem):
    __tablename__ = 'layer'
    __table_args__ = {'schema': _schema}
    __acl__ = [DENY_ALL]

    id = Column(
        Integer, ForeignKey(_schema + '.treeitem.id'), primary_key=True
    )
    public = Column(Boolean, default=True, label=_(u'Public'))
    geo_table = Column(Unicode, label=_(u'Related Postgres table'))

    def __init__(self, name=u'', public=True):
        TreeItem.__init__(self, name=name)
        self.public = public


class LayerV1(Layer):
    __label__ = _(u'layer')
    __plural__ = _(u'layers')
    __tablename__ = 'layerv1'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'layerv1'}

    id = Column(
        Integer, ForeignKey(_schema + '.layer.id'), primary_key=True
    )
    is_checked = Column(Boolean, default=True, label=_(u'Checked'))  # by default
    icon = Column(Unicode, label=_(u'Icon'))  # on the tree
    layer_type = Column(Enum(
        "internal WMS",
        "external WMS",
        "WMTS",
        "no 2D",
        native_enum=False), label=_(u'Type'))
    url = Column(Unicode, label=_(u'Base URL'))  # for externals
    image_type = Column(Enum(
        "image/jpeg",
        "image/png",
        native_enum=False), label=_(u'Image type'))  # for WMS
    style = Column(Unicode, label=_(u'Style'))
    dimensions = Column(Unicode, label=_(u'Dimensions'))  # for WMTS
    matrix_set = Column(Unicode, label=_(u'Matrix set'))  # for WMTS
    wms_url = Column(Unicode, label=_(u'WMS server URL'))  # for WMTS
    wms_layers = Column(Unicode, label=_(u'WMS layers'))  # for WMTS
    query_layers = Column(Unicode, label=_(u'Query layers'))  # for WMTS
    kml = Column(Unicode, label=_(u'KML 3D'))  # for kml 3D
    is_single_tile = Column(Boolean, label=_(u'Single tile'))  # for extenal WMS
    legend = Column(Boolean, default=True, label=_(u'Display legend'))  # on the tree
    legend_image = Column(Unicode, label=_(u'Legend image'))  # fixed legend image
    legend_rule = Column(Unicode, label=_(u'Legend rule'))  # on wms legend only one rule
    is_legend_expanded = Column(Boolean, default=False, label=_(u'Legend expanded'))
    min_resolution = Column(Float, label=_(u'Min resolution'))  # for all except internal WMS
    max_resolution = Column(Float, label=_(u'Max resolution'))  # for all except internal WMS
    disclaimer = Column(Unicode, label=_(u'Disclaimer'))
    # data attribute field in which application can find a human identifiable name or number
    identifier_attribute_field = Column(Unicode, label=_(u'Identifier attribute field'))
    exclude_properties = Column(Unicode, label=_(u'Attributes to exclude'))
    time_mode = Column(Enum(
        "disabled",
        "single",
        "range",
        native_enum=False), default="disabled", nullable=False,
        label=_(u'Time mode'))

    def __init__(
        self, name=u'', public=True, icon=u'',
        layer_type=u'internal WMS'
    ):
        Layer.__init__(self, name=name, public=public)
        self.icon = icon
        self.layer_type = layer_type


class LayerInternalWMS(Layer):
    __label__ = _(u'Internal WMS layer')
    __plural__ = _(u'Internal WMS layers')
    __tablename__ = 'layer_internal_wms'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'l_int_wms'}

    id = Column(
        Integer, ForeignKey(_schema + '.layer.id'), primary_key=True
    )
    layer = Column(Unicode, label=_(u'Layers'))
    image_type = Column(Enum(
        "image/jpeg",
        "image/png",
        native_enum=False), label=_(u'Image type'))  # for WMS
    style = Column(Unicode, label=_(u'Style'))
    time_mode = Column(Enum(
        "disabled",
        "single",
        "range",
        native_enum=False), default="disabled", nullable=False,
        label=_(u'Time mode'))

    def __init__(self, name=u'', public=True, icon=u''):
        Layer.__init__(self, name=name, public=public)


class LayerExternalWMS(Layer):
    __label__ = _(u'External WMS layer')
    __plural__ = _(u'External WMS layers')
    __tablename__ = 'layer_external_wms'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'l_ext_wms'}

    id = Column(
        Integer, ForeignKey(_schema + '.layer.id'), primary_key=True
    )
    url = Column(Unicode, label=_(u'Base URL'))
    layer = Column(Unicode, label=_(u'Layers'))
    image_type = Column(Enum(
        "image/jpeg",
        "image/png",
        native_enum=False), label=_(u'Image type'))
    style = Column(Unicode, label=_(u'Style'))
    is_single_tile = Column(Boolean, label=_(u'Single tile'))
    time_mode = Column(Enum(
        "disabled",
        "single",
        "range",
        native_enum=False), default="disabled", nullable=False,
        label=_(u'Time mode'))

    def __init__(self, name=u'', public=True):
        Layer.__init__(self, name=name, public=public)


class LayerWMTS(Layer):
    __label__ = _(u'WMTS layer')
    __plural__ = _(u'WMTS layers')
    __tablename__ = 'layer_wmts'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {'polymorphic_identity': 'l_wmts'}

    id = Column(
        Integer, ForeignKey(_schema + '.layer.id'), primary_key=True
    )
    url = Column(Unicode, label=_(u'GetCapabilities URL'))
    layer = Column(Unicode, label=_(u'Layer'))
    style = Column(Unicode, label=_(u'Style'))
    matrix_set = Column(Unicode, label=_(u'Matrix set'))

    def __init__(self, name=u'', public=True):
        Layer.__init__(self, name=name, public=public)


# association table role <> restriciton area
role_ra = Table(
    'role_restrictionarea', Base.metadata,
    Column(
        'role_id', Integer, ForeignKey(_schema + '.role.id'), primary_key=True
    ),
    Column(
        'restrictionarea_id', Integer,
        ForeignKey(_schema + '.restrictionarea.id'), primary_key=True
    ),
    schema=_schema
)

# association table layer <> restriciton area
layer_ra = Table(
    'layer_restrictionarea', Base.metadata,
    Column(
        'layer_id', Integer,
        ForeignKey(_schema + '.layer.id'), primary_key=True
    ),
    Column(
        'restrictionarea_id', Integer,
        ForeignKey(_schema + '.restrictionarea.id'), primary_key=True
    ),
    schema=_schema
)


class RestrictionArea(Base):
    __label__ = _(u'restrictionarea')
    __plural__ = _(u'restrictionareas')
    __tablename__ = 'restrictionarea'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    area = Column(Geometry('POLYGON', srid=_srid, management=management))
    name = Column(Unicode, label=_(u'Name'))
    description = Column(Unicode, label=_(u'Description'))
    readwrite = Column(Boolean, label=_(u'Read-write mode'), default=False)

    # relationship with Role and Layer
    roles = relationship(
        'Role', secondary=role_ra,
        backref='restrictionareas', cascade='save-update,merge,refresh-expire'
    )
    layers = relationship(
        'Layer', secondary=layer_ra,
        backref='restrictionareas', cascade='save-update,merge,refresh-expire'
    )

    def __init__(self, name='', description='', layers=[], roles=[],
                 area=None, readwrite=False):
        self.name = name
        self.description = description
        self.layers = layers
        self.roles = roles
        self.area = area
        self.readwrite = readwrite

    def __unicode__(self):  # pragma: nocover
        return self.name or u''

event.listen(RestrictionArea, 'after_insert', cache_invalidate_cb)
event.listen(RestrictionArea, 'after_update', cache_invalidate_cb)
event.listen(RestrictionArea, 'after_delete', cache_invalidate_cb)


# association table interface <> layer
interface_layer = Table(
    'interface_layer', Base.metadata,
    Column(
        'interface_id', Integer,
        ForeignKey(_schema + '.interface.id'), primary_key=True
    ),
    Column(
        'layer_id', Integer,
        ForeignKey(_schema + '.layer.id'), primary_key=True
    ),
    schema=_schema
)

# association table interface <> theme
interface_theme = Table(
    'interface_theme', Base.metadata,
    Column(
        'interface_id', Integer,
        ForeignKey(_schema + '.interface.id'), primary_key=True
    ),
    Column(
        'theme_id', Integer,
        ForeignKey(_schema + '.theme.id'), primary_key=True
    ),
    schema=_schema
)


class Interface(Base):
    __label__ = _(u'Interface')
    __plural__ = _(u'Interfaces')
    __tablename__ = 'interface'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, label=_(u'Name'))
    description = Column(Unicode, label=_(u'Description'))

    # relationship with Layer and Theme
    layers = relationship(
        'Layer', secondary=interface_layer,
        backref='interfaces', cascade='save-update,merge,refresh-expire'
    )
    theme = relationship(
        'Theme', secondary=interface_theme,
        backref='interfaces', cascade='save-update,merge,refresh-expire'
    )

    def __init__(self, name='', description=''):
        self.name = name
        self.description = description

    def __unicode__(self):  # pragma: nocover
        return self.name or u''


class UIMetadata(Base):
    __label__ = _(u'UI metadata')
    __plural__ = _(u'UI metadatas')
    __tablename__ = 'ui_metadata'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, label=_(u'Name'))
    value = Column(Unicode, label=_(u'Value'))
    description = Column(Unicode, label=_(u'Description'))

    item_id = Column(
        'item_id', Integer,
        ForeignKey(_schema + '.treeitem.id'), nullable=False
    )
    item = relationship("TreeItem", backref='ui_metadata')

    def __init__(self, name='', value=''):
        self.name = name
        self.value = value

    def __unicode__(self):  # pragma: nocover
        return self.name or u''


class WMTSDimension(Base):
    __label__ = _(u'WMTS dimension')
    __plural__ = _(u'WMTS dimensions')
    __tablename__ = 'wmts_dimension'
    __table_args__ = {'schema': _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, label=_(u'Name'))
    value = Column(Unicode, label=_(u'Value'))
    description = Column(Unicode, label=_(u'Description'))

    layer_id = Column(
        'layer_id', Integer,
        ForeignKey(_schema + '.layer_wmts.id'), nullable=False
    )
    layer = relationship("LayerWMTS", backref='dimensions')

    def __init__(self, name='', value=''):
        self.name = name
        self.value = value

    def __unicode__(self):  # pragma: nocover
        return self.name or u''


if _parentschema is not None and _parentschema != '':  # pragma: no cover
    class ParentRole(Base):
        __label__ = _(u'parentrole')
        __plural__ = _(u'parentroles')
        __tablename__ = 'role'
        __table_args__ = {'schema': _parentschema}
        __acl__ = [
            (Allow, AUTHORIZED_ROLE, ('view')),
        ]

        id = Column(Integer, primary_key=True)
        name = Column(Unicode, unique=True, nullable=False, label=_(u'Name'))

        def __init__(self, name=u''):
            self.name = name

        def __unicode__(self):
            return self.name or u''  # pragma: nocover


class Shorturl(Base):
    __tablename__ = 'shorturl'
    __table_args__ = {'schema': _schema + "_static"}
    __acl__ = [DENY_ALL]
    id = Column(Integer, primary_key=True)
    url = Column(Unicode)
    ref = Column(String(20), index=True, unique=True, nullable=False)
    creator_email = Column(Unicode(200))
    creation = Column(DateTime)
    last_hit = Column(DateTime)
    nb_hits = Column(Integer)
