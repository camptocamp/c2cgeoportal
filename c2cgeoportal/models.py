# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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
from hashlib import sha1

from papyrus.geo_interface import GeoInterface
from sqlalchemy import ForeignKey, Table, event
from sqlalchemy.types import Integer, Boolean, Unicode, Float, String, \
    Enum, DateTime, UserDefinedType
from sqlalchemy import UniqueConstraint
from sqlalchemy.schema import Index
from sqlalchemy.orm import relationship, backref
import sqlalchemy.ext.declarative
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Column


try:
    from pyramid.security import Allow, ALL_PERMISSIONS, DENY_ALL
# Fallback if pyramid do not exists, used by QGIS server plugin
except:  # pragma: no cover
    Allow = ALL_PERMISSIONS = DENY_ALL = None


try:
    from pyramid.i18n import TranslationStringFactory
    _ = TranslationStringFactory("c2cgeoportal")
# Fallback if pyramid do not exists, used by QGIS server plugin
except:  # pragma: no cover
    def _(s):
        return s

from c2cgeoportal import schema, srid
from c2cgeoportal.lib import caching
from c2cgeoportal.lib.sqlalchemy_ import JSONEncodedDict

__all__ = [
    "Base", "DBSession", "Functionality", "User", "Role", "TreeItem",
    "TreeGroup", "LayerGroup", "Theme", "Layer", "RestrictionArea",
    "LayerV1", "OGCServer",
    "LayerWMS", "LayerWMTS", "Interface", "Metadata", "Dimension",
    "LayergroupTreeitem"
]

log = logging.getLogger(__name__)

DBSession = None  # Initialized by pyramid_.init_dbsessions
Base = sqlalchemy.ext.declarative.declarative_base()
DBSessions = {}

AUTHORIZED_ROLE = "role_admin"

if schema is not None:
    _schema = schema
else:  # pragma: no cover
    raise Exception(
        "schema not specified, you need to add it to your config"
    )

if srid is not None:
    _srid = srid
else:  # pragma: no cover
    raise Exception(
        "srid not specified, you need to add it to your config"
    )


def cache_invalidate_cb(*args):
    caching.invalidate_region()


class TsVector(UserDefinedType):
    """ A custom type for PostgreSQL's tsvector type. """

    def get_col_spec(self):  # pragma: no cover
        return "TSVECTOR"


class FullTextSearch(GeoInterface, Base):
    __tablename__ = "tsearch"
    __table_args__ = (
        Index("tsearch_ts_idx", "ts", postgresql_using="gin"),
        {"schema": _schema}
    )
    __acl__ = [DENY_ALL]

    id = Column(Integer, primary_key=True)
    label = Column(Unicode)
    layer_name = Column(Unicode)  # Deprecated in v2
    role_id = Column(Integer, ForeignKey(_schema + ".role.id"), nullable=True)
    role = relationship("Role")
    interface_id = Column(Integer, ForeignKey(_schema + ".interface.id"), nullable=True)
    interface = relationship("Interface")
    lang = Column(String(2), nullable=True)
    public = Column(Boolean, server_default="true")
    ts = Column(TsVector)
    the_geom = Column(Geometry("GEOMETRY", srid=_srid))
    params = Column(JSONEncodedDict, nullable=True)
    actions = Column(JSONEncodedDict, nullable=True)
    from_theme = Column(Boolean, server_default="false")


class Functionality(Base):
    __tablename__ = "functionality"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    value = Column(Unicode, nullable=False)
    description = Column(Unicode)

    def __init__(self, name="", value="", description=""):
        self.name = name
        self.value = value
        self.description = description

    def __unicode__(self):
        return "{0!s} - {1!s}".format(self.name or "", self.value or "")  # pragma: no cover


event.listen(Functionality, "after_update", cache_invalidate_cb)
event.listen(Functionality, "after_delete", cache_invalidate_cb)


# association table role <> functionality
role_functionality = Table(
    "role_functionality", Base.metadata,
    Column(
        "role_id", Integer,
        ForeignKey(_schema + ".role.id"), primary_key=True
    ),
    Column(
        "functionality_id", Integer,
        ForeignKey(_schema + ".functionality.id"), primary_key=True
    ),
    schema=_schema
)

# association table theme <> functionality
theme_functionality = Table(
    "theme_functionality", Base.metadata,
    Column(
        "theme_id", Integer,
        ForeignKey(_schema + ".theme.id"), primary_key=True
    ),
    Column(
        "functionality_id", Integer,
        ForeignKey(_schema + ".functionality.id"), primary_key=True
    ),
    schema=_schema
)


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": _schema + "_static"}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    item_type = Column("type", String(10), nullable=False)
    __mapper_args__ = {
        "polymorphic_on": item_type,
        "polymorphic_identity": "user",
    }

    id = Column(Integer, primary_key=True)
    username = Column(
        Unicode, unique=True, nullable=False,
    )
    _password = Column(
        "password", Unicode, nullable=False,
    )
    temp_password = Column(
        "temp_password", Unicode, nullable=True,
    )
    email = Column(Unicode, nullable=False)
    is_password_changed = Column(Boolean, default=False)

    role_name = Column(String)
    _cached_role_name = None
    _cached_role = None

    @property
    def role(self):
        if self._cached_role_name == self.role_name:
            return self._cached_role

        if self.role_name is None or self.role_name == "":  # pragma: no cover
            self._cached_role_name = self.role_name
            self._cached_role = None
            return None

        result = self._sa_instance_state.session.query(Role).filter(
            Role.name == self.role_name
        ).all()
        if len(result) == 0:  # pragma: no cover
            self._cached_role = None
        else:
            self._cached_role = result[0]

        self._cached_role_name = self.role_name
        return self._cached_role

    def __init__(
        self, username="", password="", email="", is_password_changed=False,
        functionalities=None, role=None
    ):
        if functionalities is None:
            functionalities = []
        self.username = username
        self.password = password
        self.email = email
        self.is_password_changed = is_password_changed
        self.functionalities = functionalities
        if role is not None:
            self.role_name = role.name

    def _get_password(self):
        """returns password"""
        return self._password  # pragma: no cover

    def _set_password(self, password):
        """encrypts password on the fly."""
        self._password = self.__encrypt_password(password)

    def set_temp_password(self, password):
        """encrypts password on the fly."""
        self.temp_password = self.__encrypt_password(password)

    @staticmethod
    def __encrypt_password(password):
        """Hash the given password with SHA1."""
        return sha1(password.encode("utf8")).hexdigest()

    def validate_password(self, passwd):
        """Check the password against existing credentials.
        this method _MUST_ return a boolean.

        @param passwd: the password that was provided by the user to
        try and authenticate. This is the clear text version that we will
        need to match against the (possibly) encrypted one in the database.
        @type password: string
        """
        if self._password == self.__encrypt_password(passwd):
            return True
        if \
                self.temp_password is not None and \
                self.temp_password != "" and \
                self.temp_password == self.__encrypt_password(passwd):
            self._password = self.temp_password
            self.temp_password = None
            self.is_password_changed = True
            return True
        return False

    password = property(_get_password, _set_password)

    def __unicode__(self):
        return self.username or ""  # pragma: no cover


class Role(Base):
    __tablename__ = "role"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, unique=True, nullable=False)
    description = Column(Unicode)
    extent = Column(Geometry("POLYGON", srid=_srid))

    # functionality
    functionalities = relationship(
        "Functionality", secondary=role_functionality,
    )

    def __init__(self, name="", description="", functionalities=None, extent=None):
        if functionalities is None:
            functionalities = []
        self.name = name
        self.functionalities = functionalities
        self.extent = extent
        self.description = description

    def __unicode__(self):
        return self.name or ""  # pragma: no cover

    @property
    def bounds(self):
        if self.extent is None:
            return None
        return to_shape(self.extent).bounds


event.listen(Role.functionalities, "set", cache_invalidate_cb)
event.listen(Role.functionalities, "append", cache_invalidate_cb)
event.listen(Role.functionalities, "remove", cache_invalidate_cb)


class TreeItem(Base):
    __tablename__ = "treeitem"
    __table_args__ = (
        UniqueConstraint("type", "name"),
        {"schema": _schema},
    )
    __acl__ = [DENY_ALL]
    item_type = Column("type", String(10), nullable=False)
    __mapper_args__ = {"polymorphic_on": item_type}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    metadata_url = Column(Unicode)  # should not be used in V2
    description = Column(Unicode)

    @property
    def parents(self):  # pragma: no cover
        return [c.group for c in self.parents_relation]

    def is_in_interface(self, name):
        if not hasattr(self, "interfaces"):  # pragma: no cover
            return False

        for interface in self.interfaces:
            if interface.name == name:
                return True

        return False

    def get_metadatas(self, name):  # pragma: no cover
        return [metadata for metadata in self.metadatas if metadata.name == name]

    def __init__(self, name=""):
        self.name = name


event.listen(TreeItem, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(TreeItem, "after_update", cache_invalidate_cb, propagate=True)
event.listen(TreeItem, "after_delete", cache_invalidate_cb, propagate=True)


# association table LayerGroup <> TreeItem
class LayergroupTreeitem(Base):
    __tablename__ = "layergroup_treeitem"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    # required by formalchemy
    id = Column(Integer, primary_key=True)
    description = Column(Unicode)
    treegroup_id = Column(
        Integer, ForeignKey(_schema + ".treegroup.id")
    )
    treegroup = relationship(
        "TreeGroup",
        backref=backref(
            "children_relation",
            order_by="LayergroupTreeitem.ordering",
            cascade="save-update,merge,delete,delete-orphan",
        ),
        primaryjoin="LayergroupTreeitem.treegroup_id==TreeGroup.id",
    )
    treeitem_id = Column(
        Integer, ForeignKey(_schema + ".treeitem.id")
    )
    treeitem = relationship(
        "TreeItem",
        backref=backref(
            "parents_relation", cascade="save-update,merge,delete,delete-orphan"
        ),
        primaryjoin="LayergroupTreeitem.treeitem_id==TreeItem.id",
    )
    ordering = Column(Integer)

    def __init__(self, group=None, item=None, ordering=0):
        self.treegroup = group
        self.treeitem = item
        self.ordering = ordering


event.listen(LayergroupTreeitem, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, "after_update", cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, "after_delete", cache_invalidate_cb, propagate=True)


class TreeGroup(TreeItem):
    __tablename__ = "treegroup"
    __table_args__ = {"schema": _schema}
    __acl__ = [DENY_ALL]

    id = Column(
        Integer, ForeignKey(_schema + ".treeitem.id"), primary_key=True
    )

    def _get_children(self):
        return [c.treeitem for c in self.children_relation]

    def _set_children(self, children, order=False):
        for child in self.children_relation:
            if child.treeitem not in children:
                child.treeitem = None
                child.treegroup = None
        if order is True:  # pragma: nocover
            for index, child in enumerate(children):
                current = [c for c in self.children_relation if c.treeitem == child]
                if len(current) == 1:
                    current[0].ordering = index * 10
                else:
                    LayergroupTreeitem(self, child, index * 10)
            self.children_relation.sort(key=lambda child: child.ordering)
        else:
            current_item = [child.treeitem for child in self.children_relation]
            for index, item in enumerate(children):
                if item not in current_item:
                    LayergroupTreeitem(self, item, 1000000 + index)
            for index, child in enumerate(self.children_relation):
                child.ordering = index * 10

    children = property(_get_children, _set_children)

    def __init__(self, name=""):
        TreeItem.__init__(self, name=name)


class LayerGroup(TreeGroup):
    __tablename__ = "layergroup"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {"polymorphic_identity": "group"}

    id = Column(
        Integer, ForeignKey(_schema + ".treegroup.id"), primary_key=True
    )
    is_expanded = Column(Boolean)  # shouldn"t be used in V3
    is_internal_wms = Column(Boolean)
    # children have radio button instance of check box
    is_base_layer = Column(Boolean)  # Should not be used in V3

    def __init__(
            self, name="", is_expanded=False,
            is_internal_wms=True, is_base_layer=False):
        TreeGroup.__init__(self, name=name)
        self.is_expanded = is_expanded
        self.is_internal_wms = is_internal_wms
        self.is_base_layer = is_base_layer


# role theme link for restricted theme
restricted_role_theme = Table(
    "restricted_role_theme", Base.metadata,
    Column(
        "role_id", Integer, ForeignKey(_schema + ".role.id"), primary_key=True
    ),
    Column(
        "theme_id", Integer,
        ForeignKey(_schema + ".theme.id"), primary_key=True
    ),
    schema=_schema
)


class Theme(TreeGroup):
    __tablename__ = "theme"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {"polymorphic_identity": "theme"}

    id = Column(
        Integer, ForeignKey(_schema + ".treegroup.id"), primary_key=True
    )
    ordering = Column(Integer, nullable=False)
    public = Column(Boolean, default=True, nullable=False)
    icon = Column(Unicode)

    # functionality
    functionalities = relationship(
        "Functionality", secondary=theme_functionality,
    )

    # restricted to role
    restricted_roles = relationship(
        "Role", secondary=restricted_role_theme,
        cascade="save-update,merge,refresh-expire",
    )

    def __init__(self, name="", ordering=100, icon=""):
        TreeGroup.__init__(self, name=name)
        self.ordering = ordering
        self.icon = icon


event.listen(Theme.functionalities, "set", cache_invalidate_cb)
event.listen(Theme.functionalities, "append", cache_invalidate_cb)
event.listen(Theme.functionalities, "remove", cache_invalidate_cb)


class Layer(TreeItem):
    __tablename__ = "layer"
    __table_args__ = {"schema": _schema}
    __acl__ = [DENY_ALL]

    id = Column(
        Integer, ForeignKey(_schema + ".treeitem.id"), primary_key=True
    )
    public = Column(Boolean, default=True)
    geo_table = Column(Unicode)
    exclude_properties = Column(Unicode)

    def __init__(self, name="", public=True):
        TreeItem.__init__(self, name=name)
        self.public = public


class DimensionLayer(Layer):
    __acl__ = [DENY_ALL]


class LayerV1(Layer):  # Deprecated in v2
    __tablename__ = "layerv1"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {"polymorphic_identity": "layerv1"}

    id = Column(
        Integer, ForeignKey(_schema + ".layer.id"), primary_key=True
    )
    layer = Column(Unicode)
    is_checked = Column(Boolean, default=True)  # by default
    icon = Column(Unicode)  # on the tree
    layer_type = Column(Enum(
        "internal WMS",
        "external WMS",
        "WMTS",
        "no 2D",
        native_enum=False))
    url = Column(Unicode)  # for externals
    image_type = Column(Enum(
        "image/jpeg",
        "image/png",
        native_enum=False))  # for WMS
    style = Column(Unicode)
    dimensions = Column(Unicode)  # for WMTS
    matrix_set = Column(Unicode)  # for WMTS
    wms_url = Column(Unicode)  # for WMTS
    wms_layers = Column(Unicode)  # for WMTS
    query_layers = Column(Unicode)  # for WMTS
    kml = Column(Unicode)  # for kml 3D
    is_single_tile = Column(Boolean)  # for extenal WMS
    legend = Column(Boolean, default=True)  # on the tree
    legend_image = Column(Unicode)  # fixed legend image
    legend_rule = Column(Unicode)  # on wms legend only one rule
    is_legend_expanded = Column(Boolean, default=False)
    min_resolution = Column(Float)  # for all except internal WMS
    max_resolution = Column(Float)  # for all except internal WMS
    disclaimer = Column(Unicode)
    # data attribute field in which application can find a human identifiable name or number
    identifier_attribute_field = Column(Unicode)
    time_mode = Column(Enum(
        "disabled",
        "value",
        "range",
        native_enum=False), default="disabled", nullable=False,
    )
    time_widget = Column(Enum(
        "slider",
        "datepicker",
        native_enum=False), default="slider", nullable=True,
    )

    def __init__(
        self, name="", public=True, icon="",
        layer_type="internal WMS"
    ):
        Layer.__init__(self, name=name, public=public)
        self.layer = name
        self.icon = icon
        self.layer_type = layer_type


OGCSERVER_TYPE_MAPSERVER = "mapserver"
OGCSERVER_TYPE_QGISSERVER = "qgisserver"
OGCSERVER_TYPE_GEOSERVER = "geoserver"
OGCSERVER_TYPE_OTHER = "other"

OGCSERVER_AUTH_NOAUTH = "No auth"
OGCSERVER_AUTH_STANDARD = "Standard auth"
OGCSERVER_AUTH_GEOSERVER = "Geoserver auth"


class OGCServer(Base):
    __tablename__ = "ogc_server"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(
        Integer, primary_key=True
    )
    name = Column(Unicode, nullable=False, unique=True)
    description = Column(Unicode)
    url = Column(Unicode, nullable=False)
    url_wfs = Column(Unicode)
    type = Column(Enum(
        OGCSERVER_TYPE_MAPSERVER,
        OGCSERVER_TYPE_QGISSERVER,
        OGCSERVER_TYPE_GEOSERVER,
        OGCSERVER_TYPE_OTHER,
        native_enum=False), nullable=False)
    image_type = Column(Enum(
        "image/jpeg",
        "image/png",
        native_enum=False), nullable=False)
    auth = Column(Enum(
        OGCSERVER_AUTH_NOAUTH,
        OGCSERVER_AUTH_STANDARD,
        OGCSERVER_AUTH_GEOSERVER,
        native_enum=False), nullable=False)
    wfs_support = Column(Boolean)
    is_single_tile = Column(Boolean)

    def __init__(
        self, name="", description=None, url="https://wms.example.com", url_wfs=None,
        type_=OGCSERVER_TYPE_MAPSERVER, image_type="image/png",
        auth=OGCSERVER_AUTH_STANDARD, wfs_support=True,
        is_single_tile=False
    ):
        self.name = name
        self.description = description
        self.url = url
        self.url_wfs = url_wfs
        self.type = type_
        self.image_type = image_type
        self.auth = auth
        self.wfs_support = wfs_support
        self.is_single_tile = is_single_tile

    def __unicode__(self):
        return self.name or ""  # pragma: no cover


class LayerWMS(DimensionLayer):
    __tablename__ = "layer_wms"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {"polymorphic_identity": "l_wms"}

    id = Column(
        Integer, ForeignKey(_schema + ".layer.id"), primary_key=True
    )
    ogc_server_id = Column(
        Integer, ForeignKey(_schema + ".ogc_server.id"), nullable=False
    )
    layer = Column(Unicode)
    style = Column(Unicode)
    time_mode = Column(Enum(
        "disabled",
        "value",
        "range",
        native_enum=False), default="disabled", nullable=False,
    )
    time_widget = Column(Enum(
        "slider",
        "datepicker",
        native_enum=False), default="slider", nullable=False,
    )

    # relationship with OGCServer
    ogc_server = relationship(
        "OGCServer"
    )

    def __init__(
        self, name="", layer="", public=True, time_mode="disabled", time_widget="slider"
    ):
        DimensionLayer.__init__(self, name=name, public=public)
        self.layer = layer
        self.time_mode = time_mode
        self.time_widget = time_widget


class LayerWMTS(DimensionLayer):
    __tablename__ = "layer_wmts"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]
    __mapper_args__ = {"polymorphic_identity": "l_wmts"}

    id = Column(
        Integer, ForeignKey(_schema + ".layer.id"), primary_key=True
    )
    url = Column(Unicode, nullable=False)
    layer = Column(Unicode, nullable=False)
    style = Column(Unicode)
    matrix_set = Column(Unicode)
    image_type = Column(Enum(
        "image/jpeg",
        "image/png",
        native_enum=False), nullable=False
    )

    def __init__(self, name="", public=True, image_type="image/png"):
        DimensionLayer.__init__(self, name=name, public=public)
        self.image_type = image_type


# association table role <> restriciton area
role_ra = Table(
    "role_restrictionarea", Base.metadata,
    Column(
        "role_id", Integer, ForeignKey(_schema + ".role.id"), primary_key=True
    ),
    Column(
        "restrictionarea_id", Integer,
        ForeignKey(_schema + ".restrictionarea.id"), primary_key=True
    ),
    schema=_schema
)

# association table layer <> restriciton area
layer_ra = Table(
    "layer_restrictionarea", Base.metadata,
    Column(
        "layer_id", Integer,
        ForeignKey(_schema + ".layer.id"), primary_key=True
    ),
    Column(
        "restrictionarea_id", Integer,
        ForeignKey(_schema + ".restrictionarea.id"), primary_key=True
    ),
    schema=_schema
)


class RestrictionArea(Base):
    __tablename__ = "restrictionarea"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    area = Column(Geometry("POLYGON", srid=_srid))
    name = Column(Unicode)
    description = Column(Unicode)
    readwrite = Column(Boolean, default=False)

    # relationship with Role and Layer
    roles = relationship(
        "Role", secondary=role_ra,
        backref="restrictionareas", cascade="save-update,merge,refresh-expire"
    )
    layers = relationship(
        "Layer", secondary=layer_ra,
        backref="restrictionareas", cascade="save-update,merge,refresh-expire"
    )

    def __init__(self, name="", description="", layers=None, roles=None,
                 area=None, readwrite=False):
        if layers is None:
            layers = []
        if roles is None:
            roles = []
        self.name = name
        self.description = description
        self.layers = layers
        self.roles = roles
        self.area = area
        self.readwrite = readwrite

    def __unicode__(self):  # pragma: no cover
        return self.name or ""


event.listen(RestrictionArea, "after_insert", cache_invalidate_cb)
event.listen(RestrictionArea, "after_update", cache_invalidate_cb)
event.listen(RestrictionArea, "after_delete", cache_invalidate_cb)


# association table interface <> layer
interface_layer = Table(
    "interface_layer", Base.metadata,
    Column(
        "interface_id", Integer,
        ForeignKey(_schema + ".interface.id"), primary_key=True
    ),
    Column(
        "layer_id", Integer,
        ForeignKey(_schema + ".layer.id"), primary_key=True
    ),
    schema=_schema
)

# association table interface <> theme
interface_theme = Table(
    "interface_theme", Base.metadata,
    Column(
        "interface_id", Integer,
        ForeignKey(_schema + ".interface.id"), primary_key=True
    ),
    Column(
        "theme_id", Integer,
        ForeignKey(_schema + ".theme.id"), primary_key=True
    ),
    schema=_schema
)


class Interface(Base):
    __tablename__ = "interface"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    description = Column(Unicode)

    # relationship with Layer and Theme
    layers = relationship(
        "Layer", secondary=interface_layer,
        backref="interfaces", cascade="save-update,merge,refresh-expire"
    )
    theme = relationship(
        "Theme", secondary=interface_theme,
        backref="interfaces", cascade="save-update,merge,refresh-expire"
    )

    def __init__(self, name="", description=""):
        self.name = name
        self.description = description

    def __unicode__(self):  # pragma: no cover
        return self.name or ""


class Metadata(Base):
    __tablename__ = "metadata"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    value = Column(Unicode)
    description = Column(Unicode)

    item_id = Column(
        "item_id", Integer,
        ForeignKey(_schema + ".treeitem.id"), nullable=False
    )
    item = relationship(
        "TreeItem",
        backref=backref(
            "metadatas",
            cascade="save-update,merge,delete,delete-orphan",
        ),
    )

    def __init__(self, name="", value=""):
        self.name = name
        self.value = value

    def __unicode__(self):  # pragma: no cover
        return "{0!s}: {1!s}".format(self.name or "", self.value or "")


event.listen(Metadata, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(Metadata, "after_update", cache_invalidate_cb, propagate=True)
event.listen(Metadata, "after_delete", cache_invalidate_cb, propagate=True)


class Dimension(Base):
    __tablename__ = "dimension"
    __table_args__ = {"schema": _schema}
    __acl__ = [
        (Allow, AUTHORIZED_ROLE, ALL_PERMISSIONS),
    ]

    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    value = Column(Unicode)
    description = Column(Unicode)

    layer_id = Column(
        "layer_id", Integer,
        ForeignKey(_schema + ".layer.id"), nullable=False
    )
    layer = relationship(
        "DimensionLayer",
        backref=backref(
            "dimensions",
            cascade="save-update,merge,delete,delete-orphan",
        ),
    )

    def __init__(self, name="", value="", layer=None):
        self.name = name
        self.value = value
        if layer is not None:
            self.layer = layer

    def __unicode__(self):  # pragma: no cover
        return self.name or ""


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
