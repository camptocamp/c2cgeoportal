# -*- coding: utf-8 -*-

# Copyright (c) 2011-2020, Camptocamp SA
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
import re
from typing import Any, Dict, List, Optional, Tuple, Union, cast  # noqa, pylint: disable=unused-import

from c2c.template.config import config
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from papyrus.geo_interface import GeoInterface
from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, event
from sqlalchemy.orm import Session, backref, relationship
from sqlalchemy.schema import Index
from sqlalchemy.types import Boolean, Enum, Integer, String, Unicode

from c2cgeoportal_commons.models import Base, _, cache_invalidate_cb
from c2cgeoportal_commons.models.sqlalchemy import JSONEncodedDict, TsVector

try:
    from colander import drop
    from deform.widget import HiddenWidget, SelectWidget, TextAreaWidget
    from c2cgeoform import default_map_settings
    from c2cgeoform.ext.colander_ext import Geometry as ColanderGeometry
    from c2cgeoform.ext.deform_ext import MapWidget, RelationSelect2Widget
except ModuleNotFoundError:
    drop = None
    default_map_settings = {"srid": 3857, "view": {"projection": "EPSG:3857"}}

    class GenericClass:
        def __init__(self, *args: Any, **kwargs: Any):
            pass

    HiddenWidget = GenericClass
    MapWidget = GenericClass
    SelectWidget = GenericClass
    TextAreaWidget = GenericClass
    ColanderGeometry = GenericClass
    RelationSelect2Widget = GenericClass


LOG = logging.getLogger(__name__)

_schema: str = config["schema"] or "main"
_srid: int = cast(int, config["srid"]) or 3857

# Set some default values for the admin interface
_admin_config: Dict = config.get_config().get("admin_interface", {})
_map_config: Dict = {**default_map_settings, **_admin_config.get("map", {})}
view_srid_match = re.match(r"EPSG:(\d+)", _map_config["view"]["projection"])
if "map_srid" not in _admin_config and view_srid_match is not None:
    _admin_config["map_srid"] = view_srid_match.group(1)


class FullTextSearch(GeoInterface, Base):
    __tablename__ = "tsearch"
    __table_args__ = (Index("tsearch_ts_idx", "ts", postgresql_using="gin"), {"schema": _schema})

    id = Column(Integer, primary_key=True)
    label = Column(Unicode)
    layer_name = Column(Unicode)
    role_id = Column(Integer, ForeignKey(_schema + ".role.id", ondelete="CASCADE"), nullable=True)
    role = relationship("Role")
    interface_id = Column(Integer, ForeignKey(_schema + ".interface.id", ondelete="CASCADE"), nullable=True)
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
    __colanderalchemy_config__ = {"title": _("Functionality"), "plural": _("Functionalities")}

    __c2cgeoform_config__ = {"duplicate": True}

    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    name = Column(Unicode, nullable=False, info={"colanderalchemy": {"title": _("Name")}})
    description = Column(Unicode, info={"colanderalchemy": {"title": _("Description")}})
    value = Column(Unicode, nullable=False, info={"colanderalchemy": {"title": _("Value")}})

    def __init__(self, name: str = "", value: str = "", description: str = "") -> None:
        self.name = name
        self.value = value
        self.description = description

    def __str__(self) -> str:
        return "{} - {}".format(self.name or "", self.value or "")  # pragma: no cover


event.listen(Functionality, "after_update", cache_invalidate_cb)
event.listen(Functionality, "after_delete", cache_invalidate_cb)


# association table role <> functionality
role_functionality = Table(
    "role_functionality",
    Base.metadata,
    Column("role_id", Integer, ForeignKey(_schema + ".role.id"), primary_key=True),
    Column("functionality_id", Integer, ForeignKey(_schema + ".functionality.id"), primary_key=True),
    schema=_schema,
)

# association table theme <> functionality
theme_functionality = Table(
    "theme_functionality",
    Base.metadata,
    Column("theme_id", Integer, ForeignKey(_schema + ".theme.id"), primary_key=True),
    Column("functionality_id", Integer, ForeignKey(_schema + ".functionality.id"), primary_key=True),
    schema=_schema,
)


class Role(Base):
    __tablename__ = "role"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Role"), "plural": _("Roles")}
    __c2cgeoform_config__ = {"duplicate": True}

    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    name = Column(Unicode, unique=True, nullable=False, info={"colanderalchemy": {"title": _("Name")}})
    description = Column(Unicode, info={"colanderalchemy": {"title": _("Description")}})
    extent = Column(
        Geometry("POLYGON", srid=_srid),
        info={
            "colanderalchemy": {
                "typ": ColanderGeometry("POLYGON", srid=_srid, map_srid=_admin_config["map_srid"]),
                "widget": MapWidget(map_options=_map_config),
            }
        },
    )

    # functionality
    functionalities = relationship(
        "Functionality",
        secondary=role_functionality,
        cascade="save-update,merge,refresh-expire",
        info={"colanderalchemy": {"exclude": True, "title": _("Functionalities")}},
    )

    def __init__(
        self,
        name: str = "",
        description: str = "",
        functionalities: List[Functionality] = None,
        extent: Geometry = None,
    ) -> None:
        if functionalities is None:
            functionalities = []
        self.name = name
        self.functionalities = functionalities
        self.extent = extent
        self.description = description

    def __str__(self) -> str:
        return self.name or ""  # pragma: no cover

    @property
    def bounds(self) -> None:
        if self.extent is None:
            return None
        return to_shape(self.extent).bounds


event.listen(Role.functionalities, "set", cache_invalidate_cb)
event.listen(Role.functionalities, "append", cache_invalidate_cb)
event.listen(Role.functionalities, "remove", cache_invalidate_cb)


class TreeItem(Base):
    __tablename__ = "treeitem"
    __table_args__: Union[Tuple, Dict[str, Any]] = (
        UniqueConstraint("type", "name"),
        {"schema": _schema},
    )
    item_type = Column("type", String(10), nullable=False, info={"colanderalchemy": {"exclude": True}})
    __mapper_args__ = {"polymorphic_on": item_type}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False, info={"colanderalchemy": {"title": _("Name")}})
    description = Column(Unicode, info={"colanderalchemy": {"title": _("Description")}})

    @property
    # Better: def parents(self) -> List[TreeGroup]:  # pragma: no cover
    def parents(self) -> List["TreeItem"]:  # pragma: no cover
        return [c.group for c in self.parents_relation]

    def is_in_interface(self, name: str) -> bool:
        if not hasattr(self, "interfaces"):  # pragma: no cover
            return False

        for interface in self.interfaces:
            if interface.name == name:
                return True

        return False

    def get_metadatas(self, name: str) -> List["Metadata"]:  # pragma: no cover
        return [metadata for metadata in self.metadatas if metadata.name == name]

    def __init__(self, name: str = "") -> None:
        self.name = name


event.listen(TreeItem, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(TreeItem, "after_update", cache_invalidate_cb, propagate=True)
event.listen(TreeItem, "after_delete", cache_invalidate_cb, propagate=True)


# association table TreeGroup <> TreeItem
class LayergroupTreeitem(Base):
    __tablename__ = "layergroup_treeitem"
    __table_args__ = {"schema": _schema}

    # required by formalchemy
    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    description = Column(Unicode, info={"colanderalchemy": {"exclude": True}})
    treegroup_id = Column(
        Integer, ForeignKey(_schema + ".treegroup.id"), info={"colanderalchemy": {"exclude": True}}
    )
    treegroup = relationship(
        "TreeGroup",
        backref=backref(
            "children_relation",
            order_by="LayergroupTreeitem.ordering",
            cascade="save-update,merge,delete,delete-orphan,expunge",
            info={"colanderalchemy": {"title": _("Children"), "exclude": True}},
        ),
        primaryjoin="LayergroupTreeitem.treegroup_id==TreeGroup.id",
        info={"colanderalchemy": {"exclude": True}, "c2cgeoform": {"duplicate": False}},
    )
    treeitem_id = Column(
        Integer, ForeignKey(_schema + ".treeitem.id"), info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    treeitem = relationship(
        "TreeItem",
        backref=backref(
            "parents_relation",
            cascade="save-update,merge,delete,delete-orphan",
            info={
                "colanderalchemy": {"title": _("Parents"), "exclude": True},
                "c2cgeoform": {"duplicate": False},
            },
        ),
        primaryjoin="LayergroupTreeitem.treeitem_id==TreeItem.id",
        info={"colanderalchemy": {"exclude": True}, "c2cgeoform": {"duplicate": False}},
    )
    ordering = Column(Integer, info={"colanderalchemy": {"widget": HiddenWidget()}})

    def __init__(self, group: "TreeGroup" = None, item: TreeItem = None, ordering: int = 0) -> None:
        self.treegroup = group
        self.treeitem = item
        self.ordering = ordering


event.listen(LayergroupTreeitem, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, "after_update", cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, "after_delete", cache_invalidate_cb, propagate=True)


class TreeGroup(TreeItem):
    __tablename__ = "treegroup"
    __table_args__ = {"schema": _schema}
    __mapper_args__ = {"polymorphic_identity": "treegroup"}  # needed for _identity_class

    id = Column(Integer, ForeignKey(_schema + ".treeitem.id"), primary_key=True)

    def _get_children(self) -> List[TreeItem]:
        return [c.treeitem for c in self.children_relation]

    def _set_children(self, children: List[TreeItem], order: bool = False) -> None:
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

    def __init__(self, name: str = "") -> None:
        TreeItem.__init__(self, name=name)


class LayerGroup(TreeGroup):
    __tablename__ = "layergroup"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Layers group"), "plural": _("Layers groups")}
    __mapper_args__ = {"polymorphic_identity": "group"}
    __c2cgeoform_config__ = {"duplicate": True}

    id = Column(
        Integer,
        ForeignKey(_schema + ".treegroup.id"),
        primary_key=True,
        info={"colanderalchemy": {"missing": drop, "widget": HiddenWidget()}},
    )
    is_expanded = Column(
        Boolean, info={"colanderalchemy": {"title": _("Expanded"), "column": 2}}
    )  # shouldn't be used in V3

    def __init__(self, name: str = "", is_expanded: bool = False) -> None:
        TreeGroup.__init__(self, name=name)
        self.is_expanded = is_expanded


# role theme link for restricted theme
restricted_role_theme = Table(
    "restricted_role_theme",
    Base.metadata,
    Column("role_id", Integer, ForeignKey(_schema + ".role.id"), primary_key=True),
    Column("theme_id", Integer, ForeignKey(_schema + ".theme.id"), primary_key=True),
    schema=_schema,
)


class Theme(TreeGroup):
    __tablename__ = "theme"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Theme"), "plural": _("Themes")}
    __mapper_args__ = {"polymorphic_identity": "theme"}
    __c2cgeoform_config__ = {"duplicate": True}

    id = Column(
        Integer,
        ForeignKey(_schema + ".treegroup.id"),
        primary_key=True,
        info={"colanderalchemy": {"missing": drop, "widget": HiddenWidget()}},
    )
    ordering = Column(
        Integer, nullable=False, info={"colanderalchemy": {"title": _("Order"), "widget": HiddenWidget()}}
    )
    public = Column(Boolean, default=True, nullable=False, info={"colanderalchemy": {"title": _("Public")}})
    icon = Column(Unicode, info={"colanderalchemy": {"title": _("Icon")}})

    # functionality
    functionalities = relationship(
        "Functionality",
        secondary=theme_functionality,
        cascade="save-update,merge,refresh-expire",
        info={"colanderalchemy": {"exclude": True, "title": _("Functionalities")}},
    )

    # restricted to role
    restricted_roles = relationship(
        "Role",
        secondary=restricted_role_theme,
        cascade="save-update,merge,refresh-expire",
        info={"colanderalchemy": {"exclude": True, "title": _("Roles")}},
    )

    def __init__(self, name: str = "", ordering: int = 100, icon: str = "") -> None:
        TreeGroup.__init__(self, name=name)
        self.ordering = ordering
        self.icon = icon


event.listen(Theme.functionalities, "set", cache_invalidate_cb)
event.listen(Theme.functionalities, "append", cache_invalidate_cb)
event.listen(Theme.functionalities, "remove", cache_invalidate_cb)


class Layer(TreeItem):
    __tablename__ = "layer"
    __table_args__ = {"schema": _schema}
    __mapper_args__ = {"polymorphic_identity": "layer"}  # needed for _identity_class

    id = Column(Integer, ForeignKey(_schema + ".treeitem.id"), primary_key=True)
    public = Column(Boolean, default=True, info={"colanderalchemy": {"title": _("Public")}})
    geo_table = Column(Unicode, info={"colanderalchemy": {"title": _("Geo table")}})
    exclude_properties = Column(Unicode, info={"colanderalchemy": {"title": _("Exclude properties")}})

    def __init__(self, name: str = "", public: bool = True) -> None:
        TreeItem.__init__(self, name=name)
        self.public = public


class DimensionLayer(Layer):
    __mapper_args__ = {"polymorphic_identity": "dimensionlayer"}  # needed for _identity_class


OGCSERVER_TYPE_MAPSERVER = "mapserver"
OGCSERVER_TYPE_QGISSERVER = "qgisserver"
OGCSERVER_TYPE_GEOSERVER = "geoserver"
OGCSERVER_TYPE_ARCGIS = "arcgis"
OGCSERVER_TYPE_OTHER = "other"

OGCSERVER_AUTH_NOAUTH = "No auth"
OGCSERVER_AUTH_STANDARD = "Standard auth"
OGCSERVER_AUTH_GEOSERVER = "Geoserver auth"
OGCSERVER_AUTH_PROXY = "Proxy"


class OGCServer(Base):
    __tablename__ = "ogc_server"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("OGC Server"), "plural": _("OGC Servers")}
    __c2cgeoform_config__ = {"duplicate": True}
    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    name = Column(Unicode, info={"colanderalchemy": {"title": _("Name")}})
    description = Column(Unicode, info={"colanderalchemy": {"title": _("Description")}})
    url = Column(Unicode, nullable=False, info={"colanderalchemy": {"title": _("Basic URL")}})
    url_wfs = Column(Unicode, info={"colanderalchemy": {"title": _("WFS URL")}})
    type = Column(
        Enum(
            OGCSERVER_TYPE_MAPSERVER,
            OGCSERVER_TYPE_QGISSERVER,
            OGCSERVER_TYPE_GEOSERVER,
            OGCSERVER_TYPE_ARCGIS,
            OGCSERVER_TYPE_OTHER,
            native_enum=False,
        ),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Server type"),
                "widget": SelectWidget(
                    values=(
                        (OGCSERVER_TYPE_MAPSERVER, OGCSERVER_TYPE_MAPSERVER),
                        (OGCSERVER_TYPE_QGISSERVER, OGCSERVER_TYPE_QGISSERVER),
                        (OGCSERVER_TYPE_GEOSERVER, OGCSERVER_TYPE_GEOSERVER),
                        (OGCSERVER_TYPE_ARCGIS, OGCSERVER_TYPE_ARCGIS),
                        (OGCSERVER_TYPE_OTHER, OGCSERVER_TYPE_OTHER),
                    )
                ),
            }
        },
    )
    image_type = Column(
        Enum("image/jpeg", "image/png", native_enum=False),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Image type"),
                "widget": SelectWidget(values=(("image/jpeg", "image/jpeg"), ("image/png", "image/png"))),
                "column": 2,
            }
        },
    )
    auth = Column(
        Enum(
            OGCSERVER_AUTH_NOAUTH,
            OGCSERVER_AUTH_STANDARD,
            OGCSERVER_AUTH_GEOSERVER,
            OGCSERVER_AUTH_PROXY,
            native_enum=False,
        ),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Authentication type"),
                "widget": SelectWidget(
                    values=(
                        (OGCSERVER_AUTH_NOAUTH, OGCSERVER_AUTH_NOAUTH),
                        (OGCSERVER_AUTH_STANDARD, OGCSERVER_AUTH_STANDARD),
                        (OGCSERVER_AUTH_GEOSERVER, OGCSERVER_AUTH_GEOSERVER),
                        (OGCSERVER_AUTH_PROXY, OGCSERVER_AUTH_PROXY),
                    )
                ),
                "column": 2,
            }
        },
    )
    wfs_support = Column(Boolean, info={"colanderalchemy": {"title": _("WFS support"), "column": 2}})
    is_single_tile = Column(Boolean, info={"colanderalchemy": {"title": _("Single tile"), "column": 2}})

    def __init__(
        self,
        name: str = "",
        description: Optional[str] = None,
        url: str = "https://wms.example.com",
        url_wfs: str = None,
        type_: str = "mapserver",
        image_type: str = "image/png",
        auth: str = "Standard auth",
        wfs_support: bool = True,
        is_single_tile: bool = False,
    ) -> None:
        self.name = name
        self.description = description
        self.url = url
        self.url_wfs = url_wfs
        self.type = type_
        self.image_type = image_type
        self.auth = auth
        self.wfs_support = wfs_support
        self.is_single_tile = is_single_tile

    def __str__(self) -> str:
        return self.name or ""  # pragma: no cover


event.listen(OGCServer, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(OGCServer, "after_update", cache_invalidate_cb, propagate=True)
event.listen(OGCServer, "after_delete", cache_invalidate_cb, propagate=True)


class LayerWMS(DimensionLayer):
    __tablename__ = "layer_wms"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("WMS Layer"), "plural": _("WMS Layers")}

    __c2cgeoform_config__ = {"duplicate": True}

    __mapper_args__ = {"polymorphic_identity": "l_wms"}

    id = Column(
        Integer,
        ForeignKey(_schema + ".layer.id", ondelete="CASCADE"),
        primary_key=True,
        info={"colanderalchemy": {"missing": None, "widget": HiddenWidget()}},
    )
    ogc_server_id = Column(
        Integer,
        ForeignKey(_schema + ".ogc_server.id"),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("OGC server"),
                "column": 2,
                "widget": RelationSelect2Widget(
                    OGCServer, "id", "name", order_by="name", default_value=("", _("- Select -"))
                ),
            }
        },
    )
    layer = Column(
        Unicode, nullable=False, info={"colanderalchemy": {"title": _("WMS layer name"), "column": 2}}
    )
    style = Column(Unicode, info={"colanderalchemy": {"title": _("Style"), "column": 2}})
    time_mode = Column(
        Enum("disabled", "value", "range", native_enum=False),
        default="disabled",
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Time mode"),
                "column": 2,
                "widget": SelectWidget(
                    values=(("disabled", _("Disabled")), ("value", _("Value")), ("range", _("Range")))
                ),
            }
        },
    )
    time_widget = Column(
        Enum("slider", "datepicker", native_enum=False),
        default="slider",
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Time widget"),
                "column": 2,
                "widget": SelectWidget(values=(("slider", _("Slider")), ("datepicker", _("Datepicker")))),
            }
        },
    )

    # relationship with OGCServer
    ogc_server = relationship(
        "OGCServer", info={"colanderalchemy": {"title": _("OGC server"), "exclude": True}}
    )

    def __init__(
        self,
        name: str = "",
        layer: str = "",
        public: bool = True,
        time_mode: str = "disabled",
        time_widget: str = "slider",
    ) -> None:
        DimensionLayer.__init__(self, name=name, public=public)
        self.layer = layer
        self.time_mode = time_mode
        self.time_widget = time_widget

    @staticmethod
    def get_default(dbsession: Session) -> DimensionLayer:
        return dbsession.query(LayerWMS).filter(LayerWMS.name == "wms-defaults").one_or_none()


class LayerWMTS(DimensionLayer):
    __tablename__ = "layer_wmts"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("WMTS Layer"), "plural": _("WMTS Layers")}
    __c2cgeoform_config__ = {"duplicate": True}
    __mapper_args__ = {"polymorphic_identity": "l_wmts"}

    id = Column(
        Integer,
        ForeignKey(_schema + ".layer.id"),
        primary_key=True,
        info={"colanderalchemy": {"missing": None, "widget": HiddenWidget()}},
    )
    url = Column(
        Unicode, nullable=False, info={"colanderalchemy": {"title": _("GetCapabilities URL"), "column": 2}}
    )
    layer = Column(
        Unicode, nullable=False, info={"colanderalchemy": {"title": _("WMTS layer name"), "column": 2}}
    )
    style = Column(Unicode, info={"colanderalchemy": {"title": _("Style"), "column": 2}})
    matrix_set = Column(Unicode, info={"colanderalchemy": {"title": _("Matrix set"), "column": 2}})
    image_type = Column(
        Enum("image/jpeg", "image/png", native_enum=False),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Image type"),
                "column": 2,
                "widget": SelectWidget(values=(("image/jpeg", "image/jpeg"), ("image/png", "image/png"))),
            }
        },
    )

    def __init__(self, name: str = "", public: bool = True, image_type: str = "image/png") -> None:
        DimensionLayer.__init__(self, name=name, public=public)
        self.image_type = image_type

    @staticmethod
    def get_default(dbsession: Session) -> DimensionLayer:
        return dbsession.query(LayerWMTS).filter(LayerWMTS.name == "wmts-defaults").one_or_none()


# association table role <> restriction area
role_ra = Table(
    "role_restrictionarea",
    Base.metadata,
    Column("role_id", Integer, ForeignKey(_schema + ".role.id"), primary_key=True),
    Column("restrictionarea_id", Integer, ForeignKey(_schema + ".restrictionarea.id"), primary_key=True),
    schema=_schema,
)

# association table layer <> restriction area
layer_ra = Table(
    "layer_restrictionarea",
    Base.metadata,
    Column("layer_id", Integer, ForeignKey(_schema + ".layer.id"), primary_key=True),
    Column("restrictionarea_id", Integer, ForeignKey(_schema + ".restrictionarea.id"), primary_key=True),
    schema=_schema,
)


class LayerVectorTiles(DimensionLayer):
    __tablename__ = "layer_vectortiles"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Vector Tiles Layer"), "plural": _("Vector Tiles Layers")}

    __c2cgeoform_config__ = {"duplicate": True}

    __mapper_args__ = {"polymorphic_identity": "l_mvt"}

    id = Column(
        Integer,
        ForeignKey(_schema + ".layer.id"),
        primary_key=True,
        info={"colanderalchemy": {"missing": None, "widget": HiddenWidget()}},
    )

    style = Column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Style"),
                "description": "The path to json style. Example: https://url/style.json",
                "column": 2,
            }
        },
    )

    xyz = Column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Raster URL"),
                "description": "The raster url. Example: https://url/{z}/{x}/{y}.png",
                "column": 2,
            }
        },
    )


class RestrictionArea(Base):
    __tablename__ = "restrictionarea"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Restriction area"), "plural": _("Restriction areas")}
    __c2cgeoform_config__ = {"duplicate": True}
    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    area = Column(
        Geometry("POLYGON", srid=_srid),
        info={
            "colanderalchemy": {
                "typ": ColanderGeometry("POLYGON", srid=_srid, map_srid=_map_config["srid"]),
                "widget": MapWidget(map_options=_map_config),
            }
        },
    )

    name = Column(Unicode, info={"colanderalchemy": {"title": _("Name")}})
    description = Column(Unicode, info={"colanderalchemy": {"title": _("Description")}})
    readwrite = Column(Boolean, default=False, info={"colanderalchemy": {"title": _("Read/write")}})

    # relationship with Role and Layer
    roles = relationship(
        "Role",
        secondary=role_ra,
        info={"colanderalchemy": {"title": _("Roles"), "exclude": True}},
        cascade="save-update,merge,refresh-expire",
        backref=backref(
            "restrictionareas", info={"colanderalchemy": {"exclude": True, "title": _("Restriction areas")}}
        ),
    )
    layers = relationship(
        "Layer",
        secondary=layer_ra,
        info={"colanderalchemy": {"title": _("Layers"), "exclude": True}},
        cascade="save-update,merge,refresh-expire",
        backref=backref(
            "restrictionareas", info={"colanderalchemy": {"title": _("Restriction areas"), "exclude": True}}
        ),
    )

    def __init__(
        self,
        name: str = "",
        description: str = "",
        layers: List[Layer] = None,
        roles: List[Role] = None,
        area: Geometry = None,
        readwrite: bool = False,
    ) -> None:
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

    def __str__(self) -> str:  # pragma: no cover
        return self.name or ""


event.listen(RestrictionArea, "after_insert", cache_invalidate_cb)
event.listen(RestrictionArea, "after_update", cache_invalidate_cb)
event.listen(RestrictionArea, "after_delete", cache_invalidate_cb)


# association table interface <> layer
interface_layer = Table(
    "interface_layer",
    Base.metadata,
    Column("interface_id", Integer, ForeignKey(_schema + ".interface.id"), primary_key=True),
    Column("layer_id", Integer, ForeignKey(_schema + ".layer.id"), primary_key=True),
    schema=_schema,
)

# association table interface <> theme
interface_theme = Table(
    "interface_theme",
    Base.metadata,
    Column("interface_id", Integer, ForeignKey(_schema + ".interface.id"), primary_key=True),
    Column("theme_id", Integer, ForeignKey(_schema + ".theme.id"), primary_key=True),
    schema=_schema,
)


class Interface(Base):
    __tablename__ = "interface"
    __table_args__ = {"schema": _schema}
    __c2cgeoform_config__ = {"duplicate": True}
    __colanderalchemy_config__ = {"title": _("Interface"), "plural": _("Interfaces")}

    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    name = Column(Unicode, info={"colanderalchemy": {"title": _("Name")}})
    description = Column(Unicode, info={"colanderalchemy": {"title": _("Description")}})

    # relationship with Layer and Theme
    layers = relationship(
        "Layer",
        secondary=interface_layer,
        cascade="save-update,merge,refresh-expire",
        info={"colanderalchemy": {"title": _("Layers"), "exclude": True}, "c2cgeoform": {"duplicate": False}},
        backref=backref("interfaces", info={"colanderalchemy": {"title": _("Interfaces"), "exclude": True}}),
    )
    theme = relationship(
        "Theme",
        secondary=interface_theme,
        cascade="save-update,merge,refresh-expire",
        info={"colanderalchemy": {"title": _("Themes"), "exclude": True}, "c2cgeoform": {"duplicate": False}},
        backref=backref("interfaces", info={"colanderalchemy": {"title": _("Interfaces"), "exclude": True}}),
    )

    def __init__(self, name: str = "", description: str = "") -> None:
        self.name = name
        self.description = description

    def __str__(self) -> str:  # pragma: no cover
        return self.name or ""


class Metadata(Base):
    __tablename__ = "metadata"
    __table_args__ = {"schema": _schema}

    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    name = Column(Unicode, info={"colanderalchemy": {"title": _("Name")}})
    value = Column(Unicode, info={"colanderalchemy": {"exclude": True}})
    description = Column(
        Unicode, info={"colanderalchemy": {"title": _("Description"), "widget": TextAreaWidget()}}
    )

    item_id = Column(
        "item_id",
        Integer,
        ForeignKey(_schema + ".treeitem.id"),
        nullable=False,
        info={"colanderalchemy": {"exclude": True}, "c2cgeoform": {"duplicate": False}},
    )
    item = relationship(
        "TreeItem",
        info={"c2cgeoform": {"duplicate": False}, "colanderalchemy": {"exclude": True}},
        backref=backref(
            "metadatas",
            cascade="save-update,merge,delete,delete-orphan,expunge",
            order_by="Metadata.name",
            info={"colanderalchemy": {"title": _("Metadatas"), "exclude": True}},
        ),
    )

    def __init__(self, name: str = "", value: str = "") -> None:
        self.name = name
        self.value = value

    def __str__(self) -> str:  # pragma: no cover
        return "{}: {}".format(self.name or "", self.value or "")


event.listen(Metadata, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(Metadata, "after_update", cache_invalidate_cb, propagate=True)
event.listen(Metadata, "after_delete", cache_invalidate_cb, propagate=True)


class Dimension(Base):
    __tablename__ = "dimension"
    __table_args__ = {"schema": _schema}

    id = Column(Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}})
    name = Column(Unicode, info={"colanderalchemy": {"title": _("Name")}})
    value = Column(Unicode, info={"colanderalchemy": {"title": _("Value")}})
    field = Column(Unicode, info={"colanderalchemy": {"title": _("Field")}})
    description = Column(
        Unicode, info={"colanderalchemy": {"title": _("Description"), "widget": TextAreaWidget()}}
    )

    layer_id = Column(
        "layer_id",
        Integer,
        ForeignKey(_schema + ".layer.id"),
        nullable=False,
        info={"colanderalchemy": {"exclude": True}, "c2cgeoform": {"duplicate": False}},
    )
    layer = relationship(
        "DimensionLayer",
        info={"c2cgeoform": {"duplicate": False}, "colanderalchemy": {"exclude": True}},
        backref=backref(
            "dimensions",
            cascade="save-update,merge,delete,delete-orphan,expunge",
            info={"colanderalchemy": {"title": _("Dimensions"), "exclude": True}},
        ),
    )

    def __init__(self, name: str = "", value: str = "", layer: str = None, field: str = None) -> None:
        self.name = name
        self.value = value
        self.field = field
        if layer is not None:
            self.layer = layer

    def __str__(self) -> str:  # pragma: no cover
        return self.name or ""
