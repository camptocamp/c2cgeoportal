# Copyright (c) 2011-2025, Camptocamp SA
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


import enum
import logging
import os
import re
from datetime import datetime
from typing import Any, Literal, Optional, cast, get_args

import pyramid.request
import sqlalchemy.orm.base
from c2c.template.config import config
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from papyrus.geo_interface import GeoInterface
from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, event
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import Mapped, Session, backref, mapped_column, relationship
from sqlalchemy.schema import Index
from sqlalchemy.types import Boolean, DateTime, Enum, Integer, String, Unicode

import c2cgeoportal_commons.lib.literal
from c2cgeoportal_commons.lib.url import get_url2
from c2cgeoportal_commons.models import Base, _, cache_invalidate_cb
from c2cgeoportal_commons.models.sqlalchemy import JSONEncodedDict, TsVector

try:
    import colander
    from c2cgeoform import default_map_settings
    from c2cgeoform.ext.colander_ext import Geometry as ColanderGeometry
    from c2cgeoform.ext.deform_ext import MapWidget, RelationSelect2Widget
    from colander import drop
    from deform.widget import CheckboxWidget, HiddenWidget, SelectWidget, TextAreaWidget, TextInputWidget

    colander_null = colander.null
except ModuleNotFoundError:
    drop = None  # pylint: disable=invalid-name
    default_map_settings = {"srid": 3857, "view": {"projection": "EPSG:3857"}}
    colander_null = None  # pylint: disable=invalid-name

    class GenericClass:
        """Fallback class implementation."""

        def __init__(self, *args: Any, **kwargs: Any):
            pass

    CheckboxWidget = GenericClass
    HiddenWidget = GenericClass
    MapWidget = GenericClass  # type: ignore[misc,assignment]
    SelectWidget = GenericClass
    TextAreaWidget = GenericClass
    ColanderGeometry = GenericClass  # type: ignore[misc,assignment]
    RelationSelect2Widget = GenericClass  # type: ignore[misc,assignment]
    TextInputWidget = GenericClass


if os.environ.get("DEVELOPMENT", "0") == "1":

    def state_str(state: Any) -> str:
        """Return a string describing an instance via its InstanceState."""

        return "None" if state is None else f"<{state.class_.__name__} {state.obj()}>"

    # In the original function sqlalchemy use the id of the object that don't allow us to give some useful
    # information
    sqlalchemy.orm.base.state_str = state_str

_LOG = logging.getLogger(__name__)

_schema: str = config["schema"] or "main"
_srid: int = cast(int, config["srid"]) or 3857

# Set some default values for the admin interface
conf = config.get_config()
assert conf is not None
_admin_config: dict[str, Any] = conf.get("admin_interface", {})
_map_config: dict[str, Any] = {**default_map_settings, **_admin_config.get("map", {})}
view_srid_match = re.match(r"EPSG:(\d+)", _map_config["view"]["projection"])
if "map_srid" not in _admin_config and view_srid_match is not None:
    _admin_config["map_srid"] = view_srid_match.group(1)


class FullTextSearch(GeoInterface, Base):  # type: ignore
    """The tsearch table representation."""

    __tablename__ = "tsearch"
    __table_args__ = (
        Index("tsearch_search_index", "ts", "public", "role_id", "interface_id", "lang"),
        Index("tsearch_ts_idx", "ts", postgresql_using="gin"),
        {"schema": _schema},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(Unicode)
    layer_name: Mapped[str] = mapped_column(Unicode, nullable=True)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(_schema + ".role.id", ondelete="CASCADE"), nullable=True
    )
    role = relationship("Role")
    interface_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(_schema + ".interface.id", ondelete="CASCADE"), nullable=True
    )
    interface = relationship("Interface")
    lang: Mapped[str] = mapped_column(String(2), nullable=True)
    public: Mapped[bool] = mapped_column(Boolean, server_default="true")
    ts = mapped_column(TsVector)
    the_geom = mapped_column(Geometry("GEOMETRY", srid=_srid, spatial_index=False))
    params = mapped_column(JSONEncodedDict, nullable=True)
    actions = mapped_column(JSONEncodedDict, nullable=True)
    from_theme: Mapped[bool] = mapped_column(Boolean, server_default="false")

    def __str__(self) -> str:
        return f"{self.label}[{self.id}]"


class Functionality(Base):  # type: ignore
    """The functionality table representation."""

    __tablename__ = "functionality"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Functionality"), "plural": _("Functionalities")}

    __c2cgeoform_config__ = {"duplicate": True}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    name: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Name"),
                "description": _("Name of the functionality."),
                "widget": SelectWidget(
                    values=[("", _("- Select -"))]
                    + [
                        (f["name"], f["name"])
                        for f in sorted(
                            _admin_config.get("available_functionalities", []),
                            key=lambda f: cast(str, f["name"]),
                        )
                    ],
                ),
            }
        },
    )
    description: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Description"),
                "description": _("An optional description."),
            }
        },
    )
    value: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Value"),
                "description": _("A value for the functionality."),
            }
        },
    )

    def __init__(self, name: str = "", value: str = "", description: str = "") -> None:
        self.name = name
        self.value = value
        self.description = description

    def __str__(self) -> str:
        return f"{self.name}={self.value}[{self.id}]"


event.listen(Functionality, "after_update", cache_invalidate_cb)
event.listen(Functionality, "after_delete", cache_invalidate_cb)


# association table role <> functionality
role_functionality = Table(
    "role_functionality",
    Base.metadata,
    Column("role_id", Integer, ForeignKey(_schema + ".role.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "functionality_id",
        Integer,
        ForeignKey(_schema + ".functionality.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema=_schema,
)

# association table theme <> functionality
theme_functionality = Table(
    "theme_functionality",
    Base.metadata,
    Column("theme_id", Integer, ForeignKey(_schema + ".theme.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "functionality_id",
        Integer,
        ForeignKey(_schema + ".functionality.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema=_schema,
)


class Role(Base):  # type: ignore
    """The role table representation."""

    __tablename__ = "role"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Role"), "plural": _("Roles")}
    __c2cgeoform_config__ = {"duplicate": True}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    name: Mapped[str] = mapped_column(
        Unicode,
        unique=True,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Name"),
                "description": _("A name for this role."),
            }
        },
    )
    description: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Description"),
                "description": _("An optional description."),
            }
        },
    )
    extent = mapped_column(
        Geometry("POLYGON", srid=_srid, spatial_index=False),
        info={
            "colanderalchemy": {
                "title": _("Extent"),
                "description": _("Initial extent for this role."),
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
        info={
            "colanderalchemy": {
                "title": _("Functionalities"),
                "description": _("Functionality values for this role."),
                "exclude": True,
            }
        },
    )

    def __init__(
        self,
        name: str = "",
        description: str = "",
        functionalities: list[Functionality] | None = None,
        extent: Geometry | None = None,
    ) -> None:
        if functionalities is None:
            functionalities = []
        self.name = name
        self.functionalities = functionalities
        self.extent = extent
        self.description = description

    def __str__(self) -> str:
        return f"{self.name}[{self.id}]>"

    @property
    def bounds(self) -> tuple[float, float, float, float] | None:  # TODO
        if self.extent is None:
            return None
        return cast(tuple[float, float, float, float], to_shape(self.extent).bounds)


event.listen(Role.functionalities, "set", cache_invalidate_cb)
event.listen(Role.functionalities, "append", cache_invalidate_cb)
event.listen(Role.functionalities, "remove", cache_invalidate_cb)


class TreeItem(Base):  # type: ignore
    """The treeitem table representation."""

    __tablename__ = "treeitem"
    __table_args__: tuple[Any, ...] | dict[str, Any] = (
        UniqueConstraint("type", "name"),
        {"schema": _schema},
    )
    item_type: Mapped[str] = mapped_column(
        "type", String(10), nullable=False, info={"colanderalchemy": {"exclude": True}}
    )
    __mapper_args__ = {"polymorphic_on": item_type}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Name"),
                "description": _(
                    """
                    The name of the node, it is used through the i18n tools to display the name on the layers
                    tree.
                    """
                ),
            }
        },
    )
    description: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Description"),
                "description": _("An optional description."),
            }
        },
    )

    @property
    # Better: def parents(self) -> List[TreeGroup]:
    def parents(self) -> list["TreeItem"]:
        return [c.treegroup for c in self.parents_relation]

    def is_in_interface(self, name: str) -> bool:
        if not hasattr(self, "interfaces"):
            return False

        for interface in self.interfaces:
            if interface.name == name:
                return True

        return False

    def get_metadata(self, name: str) -> list["Metadata"]:
        return [metadata for metadata in self.metadatas if metadata.name == name]

    def __init__(self, name: str = "") -> None:
        self.name = name

    def __str__(self) -> str:
        return f"{self.name}[{self.id}]>"


event.listen(TreeItem, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(TreeItem, "after_update", cache_invalidate_cb, propagate=True)
event.listen(TreeItem, "after_delete", cache_invalidate_cb, propagate=True)


# association table TreeGroup <> TreeItem
class LayergroupTreeitem(Base):  # type: ignore
    """The layergroup_treeitem table representation."""

    __tablename__ = "layergroup_treeitem"
    __table_args__ = {"schema": _schema}

    # required by formalchemy
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    description: Mapped[str | None] = mapped_column(Unicode, info={"colanderalchemy": {"exclude": True}})
    treegroup_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".treegroup.id", name="treegroup_id_fkey"),
        nullable=False,
        info={"colanderalchemy": {"exclude": True}},
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
    treeitem_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".treeitem.id", ondelete="CASCADE"),
        nullable=False,
        info={"colanderalchemy": {"widget": HiddenWidget()}},
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
    ordering: Mapped[int] = mapped_column(Integer, info={"colanderalchemy": {"widget": HiddenWidget()}})

    def __init__(
        self, group: Optional["TreeGroup"] = None, item: TreeItem | None = None, ordering: int = 0
    ) -> None:
        self.treegroup = group
        self.treeitem = item
        self.ordering = ordering

    def __str__(self) -> str:
        return f"{self.id}"


event.listen(LayergroupTreeitem, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, "after_update", cache_invalidate_cb, propagate=True)
event.listen(LayergroupTreeitem, "after_delete", cache_invalidate_cb, propagate=True)


class TreeGroup(TreeItem):
    """The treegroup table representation."""

    __tablename__ = "treegroup"
    __table_args__ = {"schema": _schema}
    __mapper_args__ = {"polymorphic_identity": "treegroup"}  # type: ignore[dict-item] # needed for _identity_class

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".treeitem.id", ondelete="CASCADE", name="treegroup_id_fkey"),
        primary_key=True,
    )

    def _get_children(self) -> list[TreeItem]:
        return [c.treeitem for c in self.children_relation]

    def _set_children(self, children: list[TreeItem], order: bool = False) -> None:
        """
        Set the current TreeGroup children TreeItem instances.

        By managing related LayergroupTreeitem instances.

        If order is False:
            Append new children at end of current ones.

        If order is True:
            Force order of children.
        """
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
            current_children = [child.treeitem for child in self.children_relation]
            for index, item in enumerate(children):
                if item not in current_children:
                    LayergroupTreeitem(self, item, 1000000 + index)
            for index, child in enumerate(self.children_relation):
                child.ordering = index * 10

    children = property(_get_children, _set_children)

    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)


class LayerGroup(TreeGroup):
    """The layergroup table representation."""

    __tablename__ = "layergroup"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("Layers group"),
        "plural": _("Layers groups"),
        "description": c2cgeoportal_commons.lib.literal.Literal(
            _(
                """
            <div class="help-block">
                <h4>Background layers</h4>
                <p>The background layers are configured in the database, with the layer group named
                <b>background</b> (by default).</p>
                <hr>
            </div>
                """
            )
        ),
    }
    __mapper_args__ = {"polymorphic_identity": "group"}  # type: ignore[dict-item]
    __c2cgeoform_config__ = {"duplicate": True}

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".treegroup.id", ondelete="CASCADE"),
        primary_key=True,
        info={"colanderalchemy": {"missing": drop, "widget": HiddenWidget()}},
    )

    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)


# role theme link for restricted theme
restricted_role_theme = Table(
    "restricted_role_theme",
    Base.metadata,
    Column("role_id", Integer, ForeignKey(_schema + ".role.id", ondelete="CASCADE"), primary_key=True),
    Column("theme_id", Integer, ForeignKey(_schema + ".theme.id", ondelete="CASCADE"), primary_key=True),
    schema=_schema,
)


class Theme(TreeGroup):
    """The theme table representation."""

    __tablename__ = "theme"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Theme"), "plural": _("Themes")}
    __mapper_args__ = {"polymorphic_identity": "theme"}  # type: ignore[dict-item]
    __c2cgeoform_config__ = {"duplicate": True}

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".treegroup.id", ondelete="CASCADE"),
        primary_key=True,
        info={"colanderalchemy": {"missing": drop, "widget": HiddenWidget()}},
    )
    ordering: Mapped[int] = mapped_column(
        Integer, nullable=False, info={"colanderalchemy": {"title": _("Order"), "widget": HiddenWidget()}}
    )
    public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Public"),
                "description": _("Makes the theme public."),
            }
        },
    )
    icon: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Icon"),
                "description": _("The icon URL."),
                "missing": "",
            }
        },
    )

    # functionality
    functionalities = relationship(
        "Functionality",
        secondary=theme_functionality,
        cascade="save-update,merge,refresh-expire",
        info={
            "colanderalchemy": {
                "title": _("Functionalities"),
                "description": _("The linked functionalities."),
                "exclude": True,
            }
        },
    )

    # restricted to role
    restricted_roles = relationship(
        "Role",
        secondary=restricted_role_theme,
        cascade="save-update,merge,refresh-expire",
        info={
            "colanderalchemy": {
                "title": _("Roles"),
                "description": _("Users with checked roles will get access to this theme."),
                "exclude": True,
            }
        },
    )

    def __init__(self, name: str = "", ordering: int = 100, icon: str = "") -> None:
        super().__init__(name=name)
        self.ordering = ordering
        self.icon = icon


event.listen(Theme.functionalities, "set", cache_invalidate_cb)
event.listen(Theme.functionalities, "append", cache_invalidate_cb)
event.listen(Theme.functionalities, "remove", cache_invalidate_cb)


class Layer(TreeItem):
    """The layer table representation."""

    __tablename__ = "layer"
    __table_args__ = {"schema": _schema}
    __mapper_args__ = {"polymorphic_identity": "layer"}  # type: ignore[dict-item] # needed for _identity_class

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".treeitem.id", ondelete="CASCADE"),
        primary_key=True,
        info={"colanderalchemy": {"widget": HiddenWidget()}},
    )
    public: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        info={
            "colanderalchemy": {
                "title": _("Public"),
                "description": _("Makes the layer public."),
            }
        },
    )
    geo_table: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Geo table"),
                "description": _("The related database table, used by the editing module."),
            }
        },
    )
    exclude_properties: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Exclude properties"),
                "description": _(
                    """
                    The list of attributes (database columns) that should not appear in
                    the editing form so that they cannot be modified by the end user.
                    For enumerable attributes (foreign key), the column name should end with '_id'.
                    """
                ),
                "missing": "",
            }
        },
    )

    def __init__(self, name: str = "", public: bool = True) -> None:
        super().__init__(name=name)
        self.public = public


class DimensionLayer(Layer):
    """The intermediate class for the leyser with dimension."""

    __mapper_args__ = {"polymorphic_identity": "dimensionlayer"}  # type: ignore[dict-item] # needed for _identity_class


OGCServerType = Literal["mapserver", "qgisserver", "geoserver", "arcgis", "other"]
OGCSERVER_TYPE_MAPSERVER: OGCServerType = "mapserver"
OGCSERVER_TYPE_QGISSERVER: OGCServerType = "qgisserver"
OGCSERVER_TYPE_GEOSERVER: OGCServerType = "geoserver"
OGCSERVER_TYPE_ARCGIS: OGCServerType = "arcgis"
OGCSERVER_TYPE_OTHER: OGCServerType = "other"


OGCServerAuth = Literal["No auth", "Standard auth", "Geoserver auth", "Proxy"]
OGCSERVER_AUTH_NOAUTH: OGCServerAuth = "No auth"
OGCSERVER_AUTH_STANDARD: OGCServerAuth = "Standard auth"
OGCSERVER_AUTH_GEOSERVER: OGCServerAuth = "Geoserver auth"
OGCSERVER_AUTH_PROXY: OGCServerAuth = "Proxy"


ImageType = Literal["image/jpeg", "image/png"]
TimeMode = Literal["disabled", "value", "range"]
TimeWidget = Literal["slider", "datepicker"]


class OGCServer(Base):  # type: ignore
    """The ogc_server table representation."""

    __tablename__ = "ogc_server"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("OGC Server"),
        "plural": _("OGC Servers"),
        "description": c2cgeoportal_commons.lib.literal.Literal(
            _(
                """
            <div class="help-block">
                <p>This is the description of an OGC server (WMS/WFS).\n
                For one server we try to create only one request when it is possible.</p>
                <p>If you want to query the same server to get PNG and JPEG images,\n
                you should define two <code>OGC servers</code>.</p>
                <hr>
            </div>
                """
            )
        ),
    }
    __c2cgeoform_config__ = {"duplicate": True}
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    name: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        unique=True,
        info={
            "colanderalchemy": {
                "title": _("Name"),
                "description": _(
                    "The name of the OGC Server, should contains only no unaccentuated letters, numbers and _. "
                    "When you rename it don't miss to update the <code>ogcServer<code> metadata on the "
                    "WMTS and COG layers."
                ),
            }
        },
    )
    description: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Description"),
                "description": _("An optional description."),
            }
        },
    )
    url: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Basic URL"),
                "description": _("The server URL."),
            }
        },
    )
    url_wfs: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("WFS URL"),
                "description": _("The WFS server URL. If empty, the ``Basic URL`` is used."),
            }
        },
    )
    type: Mapped[OGCServerType] = mapped_column(
        Enum(*get_args(OGCServerType), native_enum=False),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Server type"),
                "description": _(
                    "The server type which is used to know which custom attribute will be used."
                ),
                "widget": SelectWidget(values=list((e, e) for e in get_args(OGCServerType))),
            }
        },
    )
    image_type: Mapped[ImageType] = mapped_column(
        Enum(*get_args(ImageType), native_enum=False),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Image type"),
                "description": _("The MIME type of the images (e.g.: ``image/png``)."),
                "widget": SelectWidget(values=list((e, e) for e in get_args(ImageType))),
                "column": 2,
            }
        },
    )
    auth: Mapped[OGCServerAuth] = mapped_column(
        Enum(*get_args(OGCServerAuth), native_enum=False),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Authentication type"),
                "description": "The kind of authentication to use.",
                "widget": SelectWidget(values=list((e, e) for e in get_args(OGCServerAuth))),
                "column": 2,
            }
        },
    )
    wfs_support: Mapped[bool] = mapped_column(
        Boolean,
        info={
            "colanderalchemy": {
                "title": _("WFS support"),
                "description": _("Whether WFS is supported by the server."),
                "column": 2,
            }
        },
    )
    is_single_tile: Mapped[bool] = mapped_column(
        Boolean,
        info={
            "colanderalchemy": {
                "title": _("Single tile"),
                "description": _("Whether to use the single tile mode (For future use)."),
                "column": 2,
            }
        },
    )

    def __init__(
        self,
        name: str = "",
        description: str | None = None,
        url: str = "https://wms.example.com",
        url_wfs: str | None = None,
        type_: OGCServerType = OGCSERVER_TYPE_MAPSERVER,
        image_type: ImageType = "image/png",
        auth: OGCServerAuth = OGCSERVER_AUTH_STANDARD,
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
        return self.name or ""

    def url_description(self, request: pyramid.request.Request) -> str:
        errors: set[str] = set()
        url = get_url2(self.name, self.url, request, errors)
        return url.url() if url else "\n".join(errors)

    def url_wfs_description(self, request: pyramid.request.Request) -> str | None:
        if not self.url_wfs:
            return self.url_description(request)
        errors: set[str] = set()
        url = get_url2(self.name, self.url_wfs, request, errors)
        return url.url() if url else "\n".join(errors)


class LayerWMS(DimensionLayer):
    """The layer_wms table representation."""

    __tablename__ = "layer_wms"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("WMS Layer"),
        "plural": _("WMS Layers"),
        "description": c2cgeoportal_commons.lib.literal.Literal(
            _(
                """
            <div class="help-block">
                <p>Definition of a <code>WMS Layer</code>.</p>
                <p>Note: The layers named <code>wms-defaults</code> contains the values
                used when we create a new <code>WMS layer</code>.</p>
                <hr>
            </div>
                """
            )
        ),
    }

    __c2cgeoform_config__ = {"duplicate": True}

    __mapper_args__ = {"polymorphic_identity": "l_wms"}  # type: ignore[dict-item]

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".layer.id", ondelete="CASCADE"),
        primary_key=True,
        info={"colanderalchemy": {"missing": None, "widget": HiddenWidget()}},
    )
    ogc_server_id: Mapped[int] = mapped_column(
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
    layer: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("WMS layer name"),
                "description": _(
                    """
                    The WMS layers. Can be one layer, one group, or a comma separated list of layers.
                    In the case of a comma separated list of layers, you will get the legend rule for the
                    layer icon on the first layer, and to support the legend you should define a legend
                    metadata.
                    """
                ),
                "column": 2,
            }
        },
    )
    style: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Style"),
                "description": _("The style to use for this layer, can be empty."),
                "column": 2,
            }
        },
    )
    valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Valid"),
                "description": _("The status reported by latest synchronization (readonly)."),
                "column": 2,
                "widget": CheckboxWidget(readonly=True),
                "missing": colander_null,
            }
        },
    )
    invalid_reason: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Reason why I am not valid"),
                "description": _("The reason for status reported by latest synchronization (readonly)."),
                "column": 2,
                "widget": TextInputWidget(readonly=True),
                "missing": "",
            }
        },
    )
    time_mode: Mapped[TimeMode] = mapped_column(
        Enum(*get_args(TimeMode), native_enum=False),
        default="disabled",
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Time mode"),
                "description": _("Used for the WMS time component."),
                "column": 2,
                "widget": SelectWidget(
                    values=(("disabled", _("Disabled")), ("value", _("Value")), ("range", _("Range")))
                ),
            }
        },
    )
    time_widget: Mapped[TimeWidget] = mapped_column(
        Enum(*get_args(TimeWidget), native_enum=False),
        default="slider",
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Time widget"),
                "description": _("The component type used for the WMS time."),
                "column": 2,
                "widget": SelectWidget(values=(("slider", _("Slider")), ("datepicker", _("Datepicker")))),
            }
        },
    )

    # relationship with OGCServer
    ogc_server = relationship(
        "OGCServer",
        backref=backref("layers", info={"colanderalchemy": {"exclude": True, "title": _("WMS Layers")}}),
        info={
            "colanderalchemy": {
                "title": _("OGC server"),
                "description": _("The OGC server to use for this layer."),
                "exclude": True,
            }
        },
    )

    def __init__(
        self,
        name: str = "",
        layer: str = "",
        public: bool = True,
        time_mode: TimeMode = "disabled",
        time_widget: TimeWidget = "slider",
    ) -> None:
        super().__init__(name=name, public=public)
        self.layer = layer
        self.time_mode = time_mode
        self.time_widget = time_widget

    @staticmethod
    def get_default(dbsession: Session) -> DimensionLayer | None:
        return cast(
            Optional[DimensionLayer],
            dbsession.query(LayerWMS).filter(LayerWMS.name == "wms-defaults").one_or_none(),
        )


class LayerWMTS(DimensionLayer):
    """The layer_wmts table representation."""

    __tablename__ = "layer_wmts"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("WMTS Layer"),
        "plural": _("WMTS Layers"),
        "description": c2cgeoportal_commons.lib.literal.Literal(
            _(
                """
            <div class="help-block">
                <p>Definition of a <code>WMTS Layer</code>.</p>
                <p>Note: The layers named <code>wmts-defaults</code> contains the values used when
                    we create a new <code>WMTS layer</code>.</p>

                <h4>Self generated WMTS tiles</h4>
                <p>When using self generated WMTS tiles, you should use URL
                    <code>config://local/tiles/1.0.0/WMTSCapabilities.xml</code> where:<p>
                <ul>
                    <li><code>config://local</code> is a dynamic path based on the project
                        configuration.</li>
                    <li><code>/tiles</code> is a proxy in the tilecloudchain container.</li>
                </ul>

                <h4>Queryable WMTS</h4>
                <p>To make the WMTS queryable, you should add the following <code>Metadata</code>:
                <ul>
                    <li><code>ogcServer</code> with the name of the used <code>OGC server</code>,
                    <li><code>wmsLayers</code> or <code>queryLayers</code> with the layers to query
                        (comma separated list. Groups are not supported).
                </ul>
                <p>By default the scale limits for the queryable layers are the
                    <code>minResolution</code> and/or the <code>maxResolution</code>a metadata
                    value(s) of the WMTS layer. These values correspond to the WMTS layer
                    resolution(s) which should be the zoom limit.
                    You can also set a <code>minQueryResolution</code> and/or a
                    <code>maxQueryResolution</code> to set a query zoom limits independent of the
                    WMTS layer.</p>

                <h4>Print WMTS in high quality</h4>
                <p>To print the layers in high quality, you can define that the image shall be
                    retrieved with a <code>GetMap</code> on the original WMS server.
                <p>To activate this, you should add the following <code>Metadata</code>:</p>
                <ul>
                    <li><code>ogcServer</code> with the name of the used <code>OGC server</code>,</li>
                    <li><code>wmsLayers</code> or <code>printLayers</code> with the layers to print
                        (comma separated list).</li>
                </ul>
                <hr>
            </div>
                """
            )
        ),
    }
    __c2cgeoform_config__ = {"duplicate": True}
    __mapper_args__ = {"polymorphic_identity": "l_wmts"}  # type: ignore[dict-item]

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".layer.id", ondelete="CASCADE"),
        primary_key=True,
        info={"colanderalchemy": {"missing": None, "widget": HiddenWidget()}},
    )
    url: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("GetCapabilities URL"),
                "description": _("The URL to the WMTS capabilities."),
                "column": 2,
            }
        },
    )
    layer: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("WMTS layer name"),
                "description": _("The name of the WMTS layer to use."),
                "column": 2,
            }
        },
    )
    style: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Style"),
                "description": _("The style to use; if not present, the default style is used."),
                "column": 2,
                "missing": "",
            }
        },
    )
    matrix_set: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Matrix set"),
                "description": _(
                    "The matrix set to use; if there is only one matrix set in the capabilities, it can be"
                    "left empty."
                ),
                "column": 2,
                "missing": "",
            }
        },
    )
    image_type: Mapped[ImageType] = mapped_column(
        Enum(*get_args(ImageType), native_enum=False),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Image type"),
                "description": c2cgeoportal_commons.lib.literal.Literal(
                    _(
                        """
                        The MIME type of the images (e.g.: <code>image/png</code>).
                        """
                    )
                ),
                "column": 2,
                "widget": SelectWidget(values=list((e, e) for e in get_args(ImageType))),
            }
        },
    )

    def __init__(self, name: str = "", public: bool = True, image_type: ImageType = "image/png") -> None:
        super().__init__(name=name, public=public)
        self.image_type = image_type

    @staticmethod
    def get_default(dbsession: Session) -> DimensionLayer | None:
        return cast(
            Optional[DimensionLayer],
            dbsession.query(LayerWMTS).filter(LayerWMTS.name == "wmts-defaults").one_or_none(),
        )


# association table role <> restriction area
role_ra = Table(
    "role_restrictionarea",
    Base.metadata,
    Column("role_id", Integer, ForeignKey(_schema + ".role.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "restrictionarea_id",
        Integer,
        ForeignKey(_schema + ".restrictionarea.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema=_schema,
)

# association table layer <> restriction area
layer_ra = Table(
    "layer_restrictionarea",
    Base.metadata,
    Column("layer_id", Integer, ForeignKey(_schema + ".layer.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "restrictionarea_id",
        Integer,
        ForeignKey(_schema + ".restrictionarea.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema=_schema,
)


class LayerCOG(Layer):
    """The Cloud Optimized GeoTIFF layer table representation."""

    __tablename__ = "layer_cog"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("COG Layer"),
        "plural": _("COG Layers"),
        "description": c2cgeoportal_commons.lib.literal.Literal(
            _(
                """
            <div class="help-block">
                <p>Definition of a <code>COG Layer</code> (COG for
                <a href="https://www.cogeo.org/">Cloud Optimized GeoTIFF</a>).</p>
                <p>Note: The layers named <code>cog-defaults</code> contains the values
                used when we create a new <code>COG layer</code>.</p>
            </div>
                """
            )
        ),
    }
    __c2cgeoform_config__ = {"duplicate": True}
    __mapper_args__ = {"polymorphic_identity": "l_cog"}  # type: ignore[dict-item]

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".layer.id"),
        primary_key=True,
        info={"colanderalchemy": {"missing": None, "widget": HiddenWidget()}},
    )
    url: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("URL"),
                "description": _("URL of the COG file."),
                "column": 2,
            }
        },
    )

    @staticmethod
    def get_default(dbsession: Session) -> Layer | None:
        return dbsession.query(LayerCOG).filter(LayerCOG.name == "cog-defaults").one_or_none()

    def url_description(self, request: pyramid.request.Request) -> str:
        errors: set[str] = set()
        url = get_url2(self.name, self.url, request, errors)
        return url.url() if url else "\n".join(errors)


class LayerVectorTiles(DimensionLayer):
    """The layer_vectortiles table representation."""

    __tablename__ = "layer_vectortiles"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("Vector Tiles Layer"),
        "plural": _("Vector Tiles Layers"),
        "description": c2cgeoportal_commons.lib.literal.Literal(
            _(
                """
            <div class="help-block">
                <p>Definition of a <code>Vector Tiles Layer</code>.</p>
                <p>Note: The layers named <code>vector-tiles-defaults</code> contains the values used when
                    we create a new <code>Vector Tiles layer</code>.</p>

                <h4>Queryable Vector Tiles</h4>
                <p>To make the Vector Tiles queryable, you should add the following <code>Metadata</code>:
                <ul>
                    <li><code>ogcServer</code> with the name of the used <code>OGC server</code>,
                    <li><code>wmsLayers</code> or <code>queryLayers</code> with the layers to query
                        (comma separated list. Groups are not supported).
                </ul>

                <h4>Print Vector Tiles in high quality</h4>
                <p>To print the layers in high quality, you can define that the image shall be
                    retrieved with a <code>GetMap</code> on the original WMS server.
                <p>To activate this, you should add the following <code>Metadata</code>:</p>
                <ul>
                    <li><code>ogcServer</code> with the name of the used <code>OGC server</code>,</li>
                    <li><code>wmsLayers</code> or <code>printLayers</code> with the layers to print
                        (comma separated list).</li>
                </ul>
                <hr>
            </div>
                """
            )
        ),
    }

    __c2cgeoform_config__ = {"duplicate": True}

    __mapper_args__ = {"polymorphic_identity": "l_mvt"}  # type: ignore[dict-item]

    id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(_schema + ".layer.id"),
        primary_key=True,
        info={"colanderalchemy": {"missing": None, "widget": HiddenWidget()}},
    )

    style: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Style"),
                "description": _(
                    """
                    The path to a Mapbox Style file (version 8 or higher). Example: https://url/style.json.
                    """
                ),
                "column": 2,
            }
        },
    )

    sql: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("SQL query"),
                "description": _("A SQL query to get the vector tiles data."),
                "column": 2,
                "widget": TextAreaWidget(rows=15),
            }
        },
    )

    xyz: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Raster URL"),
                "description": _(
                    """
                    The raster url. Example: https://url/{z}/{x}/{y}.png. Alternative to print the
                    layer with a service which rasterises the vector tiles.
                    """
                ),
                "column": 2,
            }
        },
    )

    def __init__(self, name: str = "", public: bool = True, style: str = "", sql: str = "") -> None:
        super().__init__(name=name, public=public)
        self.style = style
        self.sql = sql

    @staticmethod
    def get_default(dbsession: Session) -> DimensionLayer | None:
        return cast(
            Optional[DimensionLayer],
            dbsession.query(LayerVectorTiles)
            .filter(LayerVectorTiles.name == "vector-tiles-defaults")
            .one_or_none(),
        )

    def style_description(self, request: pyramid.request.Request) -> str:
        errors: set[str] = set()
        url = get_url2(self.name, self.style, request, errors)
        return url.url() if url else "\n".join(errors)


class RestrictionArea(Base):  # type: ignore
    """The restrictionarea table representation."""

    __tablename__ = "restrictionarea"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {"title": _("Restriction area"), "plural": _("Restriction areas")}
    __c2cgeoform_config__ = {"duplicate": True}
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )

    name: Mapped[str] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Name"),
                "description": _("A name."),
            }
        },
    )
    description: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Description"),
                "description": _("An optional description."),
            }
        },
    )
    readwrite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        info={
            "colanderalchemy": {
                "title": _("Read/write"),
                "description": _("Allows the linked users to change the objects."),
            }
        },
    )
    area = mapped_column(
        Geometry("POLYGON", srid=_srid),
        info={
            "colanderalchemy": {
                "title": _("Area"),
                "description": _("Active in the following area, if not defined, it is active everywhere."),
                "typ": ColanderGeometry("POLYGON", srid=_srid, map_srid=_map_config["srid"]),
                "widget": MapWidget(map_options=_map_config),
            }
        },
    )

    # relationship with Role and Layer
    roles = relationship(
        "Role",
        secondary=role_ra,
        info={
            "colanderalchemy": {
                "title": _("Roles"),
                "description": _("Checked roles will grant access to this restriction area."),
                "exclude": True,
            }
        },
        cascade="save-update,merge,refresh-expire",
        backref=backref(
            "restrictionareas",
            info={
                "colanderalchemy": {
                    "title": _("Restriction areas"),
                    "description": _(
                        "Users with this role will be granted with access to those restriction areas."
                    ),
                    "exclude": True,
                }
            },
        ),
    )
    layers = relationship(
        "Layer",
        secondary=layer_ra,
        order_by=Layer.name,
        info={
            "colanderalchemy": {
                "title": _("Layers"),
                "exclude": True,
                "description": c2cgeoportal_commons.lib.literal.Literal(
                    _(
                        """
                        <div class="help-block">
                            <p>This restriction area will grant access to the checked layers.</p>
                            <hr>
                        </div>
                        """
                    )
                ),
            }
        },
        cascade="save-update,merge,refresh-expire",
        backref=backref(
            "restrictionareas",
            info={
                "colanderalchemy": {
                    "title": _("Restriction areas"),
                    "exclude": True,
                    "description": _("The areas through which the user can see the layer."),
                }
            },
        ),
    )

    def __init__(
        self,
        name: str = "",
        description: str = "",
        layers: list[Layer] | None = None,
        roles: list[Role] | None = None,
        area: Geometry | None = None,
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

    def __str__(self) -> str:
        return f"{self.name}[{self.id}]"


event.listen(RestrictionArea, "after_insert", cache_invalidate_cb)
event.listen(RestrictionArea, "after_update", cache_invalidate_cb)
event.listen(RestrictionArea, "after_delete", cache_invalidate_cb)


# association table interface <> layer
interface_layer = Table(
    "interface_layer",
    Base.metadata,
    Column(
        "interface_id", Integer, ForeignKey(_schema + ".interface.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("layer_id", Integer, ForeignKey(_schema + ".layer.id", ondelete="CASCADE"), primary_key=True),
    schema=_schema,
)

# association table interface <> theme
interface_theme = Table(
    "interface_theme",
    Base.metadata,
    Column(
        "interface_id", Integer, ForeignKey(_schema + ".interface.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("theme_id", Integer, ForeignKey(_schema + ".theme.id", ondelete="CASCADE"), primary_key=True),
    schema=_schema,
)


class Interface(Base):  # type: ignore
    """The interface table representation."""

    __tablename__ = "interface"
    __table_args__ = {"schema": _schema}
    __c2cgeoform_config__ = {"duplicate": True}
    __colanderalchemy_config__ = {"title": _("Interface"), "plural": _("Interfaces")}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    name: Mapped[str] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Name"),
                "description": _("The name of the interface, as used in request URL."),
            }
        },
    )
    description: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Description"),
                "description": _("An optional description."),
            }
        },
    )

    # relationship with Layer and Theme
    layers = relationship(
        "Layer",
        secondary=interface_layer,
        cascade="save-update,merge,refresh-expire",
        info={"colanderalchemy": {"title": _("Layers"), "exclude": True}, "c2cgeoform": {"duplicate": False}},
        backref=backref(
            "interfaces",
            info={
                "colanderalchemy": {
                    "title": _("Interfaces"),
                    "exclude": True,
                    "description": _("Make it visible in the checked interfaces."),
                }
            },
        ),
    )
    theme = relationship(
        "Theme",
        secondary=interface_theme,
        cascade="save-update,merge,refresh-expire",
        info={"colanderalchemy": {"title": _("Themes"), "exclude": True}, "c2cgeoform": {"duplicate": False}},
        backref=backref(
            "interfaces",
            info={
                "colanderalchemy": {
                    "title": _("Interfaces"),
                    "description": _("Make it visible in the checked interfaces."),
                    "exclude": True,
                }
            },
        ),
    )

    def __init__(self, name: str = "", description: str = "") -> None:
        self.name = name
        self.description = description

    def __str__(self) -> str:
        return f"{self.name}[{self.id}]"


class Metadata(Base):  # type: ignore
    """The metadata table representation."""

    __tablename__ = "metadata"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("Metadata"),
        "plural": _("Metadatas"),
    }

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    name: Mapped[str] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Name"),
                "description": c2cgeoportal_commons.lib.literal.Literal(
                    _("The type of <code>Metadata</code> we want to set.")
                ),
            }
        },
    )
    value: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Value"),
                "exclude": True,
                "description": _("The value of the metadata entry."),
            }
        },
    )
    description: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Description"),
                "widget": TextAreaWidget(),
                "description": _("An optional description."),
            }
        },
    )

    item_id: Mapped[int] = mapped_column(
        "item_id",
        Integer,
        ForeignKey(_schema + ".treeitem.id", ondelete="CASCADE"),
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
            info={
                "colanderalchemy": {
                    "title": _("Metadatas"),
                    "description": c2cgeoportal_commons.lib.literal.Literal(
                        _(
                            """
        <div class="help-block">
            <p>You can associate metadata to all theme elements (tree items).
                The purpose of this metadata is to trigger specific features, mainly UI features.
                Each metadata entry has the following attributes:</p>
            <p>The available names are configured in the <code>vars.yaml</code>
                files in <code>admin_interface/available_metadata</code>.</p>
            <p>To set a metadata entry, create or edit an entry in the Metadata view of the
                administration UI.
                Regarding effect on the referenced tree item on the client side,
                you will find an official description for each sort of metadata in the
                <code>GmfMetaData</code> definition in <code>themes.js</code>
                <a target="_blank" href="${url}">see ngeo documentation</a>.</p>
            <hr>
        </div>
                            """,
                            mapping={
                                "url": (
                                    "https://camptocamp.github.io/ngeo/"
                                    f"{os.environ.get('MAJOR_VERSION', 'master')}"
                                    "/apidoc/interfaces/contribs_gmf_src_themes.GmfMetaData.html"
                                )
                            },
                        )
                    ),
                    "exclude": True,
                }
            },
        ),
    )

    def __init__(self, name: str = "", value: str = "", description: str | None = None) -> None:
        self.name = name
        self.value = value
        self.description = description

    def __str__(self) -> str:
        return f"{self.name}={self.value}[{self.id}]"


event.listen(Metadata, "after_insert", cache_invalidate_cb, propagate=True)
event.listen(Metadata, "after_update", cache_invalidate_cb, propagate=True)
event.listen(Metadata, "after_delete", cache_invalidate_cb, propagate=True)


class Dimension(Base):  # type: ignore
    """The dimension table representation."""

    __tablename__ = "dimension"
    __table_args__ = {"schema": _schema}
    __colanderalchemy_config__ = {
        "title": _("Dimension"),
        "plural": _("Dimensions"),
    }

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, info={"colanderalchemy": {"widget": HiddenWidget()}}
    )
    name: Mapped[str] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Name"),
                "description": _("The name of the dimension as it will be sent in requests."),
            }
        },
    )
    value: Mapped[str] = mapped_column(
        Unicode,
        nullable=True,
        info={
            "colanderalchemy": {
                "title": _("Value"),
                "description": _("The default value for this dimension."),
            }
        },
    )
    field: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Field"),
                "description": _(
                    "The name of the field to use for filtering (leave empty when not using OGC filters)."
                ),
            }
        },
    )
    description: Mapped[str | None] = mapped_column(
        Unicode,
        info={
            "colanderalchemy": {
                "title": _("Description"),
                "description": _("An optional description."),
                "widget": TextAreaWidget(),
            }
        },
    )

    layer_id: Mapped[int] = mapped_column(
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
            info={
                "colanderalchemy": {
                    "title": _("Dimensions"),
                    "exclude": True,
                    "description": c2cgeoportal_commons.lib.literal.Literal(
                        _(
                            """
        <div class="help-block">
            <p>The dimensions, if not provided default values are used.</p>
            <hr>
        </div>
                            """
                        )
                    ),
                }
            },
        ),
    )

    def __init__(
        self,
        name: str = "",
        value: str = "",
        layer: str | None = None,
        field: str | None = None,
        description: str | None = None,
    ) -> None:
        self.name = name
        self.value = value
        self.field = field
        if layer is not None:
            self.layer = layer
        self.description = description

    def __str__(self) -> str:
        return f"{self.name}={self.value}[{self.id}]"


class LogAction(enum.Enum):
    """The log action enumeration."""

    INSERT = enum.auto()
    UPDATE = enum.auto()
    DELETE = enum.auto()
    SYNCHRONIZE = enum.auto()
    CONVERT_TO_WMTS = enum.auto()
    CONVERT_TO_WMS = enum.auto()


class AbstractLog(AbstractConcreteBase, Base):  # type: ignore
    """The abstract log table representation."""

    strict_attrs = True
    __colanderalchemy_config__ = {
        "title": _("Log"),
        "plural": _("Logs"),
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True, info={"colanderalchemy": {}})
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Date"),
            }
        },
    )
    action: Mapped[LogAction] = mapped_column(
        Enum(LogAction, native_enum=False),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Action"),
            }
        },
    )
    element_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Element type"),
            }
        },
    )
    element_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Element identifier"),
            }
        },
    )
    element_name: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Element name"),
            }
        },
    )
    element_url_table: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Table segment of the element URL"),
            }
        },
    )
    username: Mapped[str] = mapped_column(
        Unicode,
        nullable=False,
        info={
            "colanderalchemy": {
                "title": _("Username"),
            }
        },
    )


class Log(AbstractLog):
    """The main log table representation."""

    __tablename__ = "log"
    __table_args__ = {"schema": _schema}
    __mapper_args__ = {
        "polymorphic_identity": "main",
        "concrete": True,
    }
