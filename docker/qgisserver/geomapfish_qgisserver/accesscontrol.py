# Copyright (c) 2018-2025, Camptocamp SA
# All rights reserved.

# This program is free software; you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.

import logging
import os
import random
import re
from enum import Enum
from threading import Lock
from typing import TYPE_CHECKING, Any, Optional, cast

import c2cwsgiutils.broadcast
import geoalchemy2
import qgis.server
import sqlalchemy
import yaml
import zope.event.classhandler
from c2c.template.config import config
from c2cgeoportal_commons.lib.url import Url, get_url2
from qgis.core import (
    QgsDataSourceUri,
    QgsFeature,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsLayerTreeNode,
    QgsProject,
    QgsVectorLayer,
)
from qgis.server import QgsAccessControlFilter, QgsConfigCache
from shapely import ops, wkb
from shapely.geometry.base import BaseGeometry
from sqlalchemy.orm import configure_mappers, joinedload, sessionmaker, subqueryload
from sqlalchemy.orm.session import Session

if TYPE_CHECKING:
    from c2cgeoportal_commons.models import (
        main,  # pylint: disable=ungrouped-imports,useless-suppression
    )

_LOG = logging.getLogger(__name__)


def create_session_factory(url: str, configuration: dict[str, Any]) -> sessionmaker:
    """Create a SQLAlchemy session factory."""
    configure_mappers()
    db_match = re.match(".*(@[^@]+)$", url)
    _LOG.info(
        "Connect to the database: ***%s, with config: %s",
        db_match.group(1) if db_match else "",
        ", ".join([f"{e[0]}={e[1]}" for e in configuration.items()]),
    )
    engine = sqlalchemy.create_engine(url, **configuration)
    session_factory = sessionmaker()
    session_factory.configure(bind=engine)
    return session_factory


class GMFException(Exception):
    """Standard exception."""


class Access(Enum):
    """Access mode."""

    NO = 1
    AREA = 2
    FULL = 3


class GeoMapFishAccessControl(QgsAccessControlFilter):
    """Implements GeoMapFish access restriction."""

    def __init__(self, server_iface: qgis.server.QgsServerInterface):
        """Initialize the plugin."""
        super().__init__(server_iface)

        self.server_iface = server_iface
        self.initialized = False

        try:
            config.init(os.environ.get("GEOMAPFISH_CONFIG", "/etc/qgisserver/geomapfish.yaml"))

            c2cwsgiutils.broadcast.init()

            configuration = config.get_config()
            assert configuration is not None

            DBSession = create_session_factory(  # pylint: disable=invalid-name
                config.get("sqlalchemy_slave.url"), configuration.get("sqlalchemy", {})
            )

            if "GEOMAPFISH_OGCSERVER" in os.environ:
                self.single = True
                self.ogcserver_accesscontrol = OGCServerAccessControl(
                    server_iface,
                    os.environ["GEOMAPFISH_OGCSERVER"],
                    os.environ["QGIS_PROJECT_FILE"],
                    config.get("srid"),
                    DBSession,
                )

                _LOG.info("Use OGC server named '%s'.", os.environ["GEOMAPFISH_OGCSERVER"])
                self.initialized = True
            elif "GEOMAPFISH_ACCESSCONTROL_CONFIG" in os.environ:
                self.single = False
                self.ogcserver_accesscontrols = {}
                with open(os.environ["GEOMAPFISH_ACCESSCONTROL_CONFIG"], encoding="utf-8") as ac_config_file:
                    ac_config = yaml.safe_load(ac_config_file.read())

                for map_, map_config in ac_config.get("map_config").items():
                    map_config["access_control"] = OGCServerAccessControl(
                        server_iface, map_config["ogc_server"], map_, config.get("srid"), DBSession
                    )
                    self.ogcserver_accesscontrols[map_] = map_config
                _LOG.info("Use config '%s'.", os.environ["GEOMAPFISH_ACCESSCONTROL_CONFIG"])
                self.initialized = True
            elif "GEOMAPFISH_ACCESSCONTROL_BASE_URL" in os.environ:
                self.ogcserver_accesscontrols = {}
                single_ogc_server = None
                base_url = Url(os.environ["GEOMAPFISH_ACCESSCONTROL_BASE_URL"])
                session = DBSession()
                try:
                    from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
                        OGCServer,
                    )

                    for ogcserver in session.query(OGCServer).all():
                        errors: set[str] = set()
                        url = get_url2(
                            f"The OGC server '{ogcserver.name}'",
                            ogcserver.url,
                            None,
                            errors,
                            configuration.get("servers", {}),
                        )

                        if errors:
                            _LOG.warning(
                                "Ignoring OGC server '%s', get error on parsing URL:\n%s",
                                ogcserver.name,
                                "\n".join(errors),
                            )
                            continue
                        if url is None:
                            _LOG.warning("Ignoring OGC server '%s', the URL is None", ogcserver.name)
                            continue
                        if (
                            base_url.scheme == url.scheme
                            and base_url.netloc == url.netloc
                            and base_url.path == url.path
                        ):
                            query = url.query_lower
                            if "map" not in query:
                                if single_ogc_server is None:
                                    single_ogc_server = ogcserver
                                    _LOG.debug(
                                        "OGC server '%s', 'map' is not in the parameters => single server?",
                                        ogcserver.name,
                                    )
                                else:
                                    _LOG.error(
                                        "OGC server '%s', 'map' is not in the parameters and we already "
                                        "have a single OCG server '%s'",
                                        ogcserver.name,
                                        single_ogc_server.name,
                                    )
                                continue

                            map_ = url.query_lower["map"]
                            self.ogcserver_accesscontrols[map_] = {
                                "ogcserver": ogcserver.name,
                                "access_control": OGCServerAccessControl(
                                    server_iface,
                                    ogcserver.name,
                                    map_,
                                    config.get("srid"),
                                    DBSession,
                                    ogcserver=ogcserver,
                                ),
                            }
                            _LOG.info("OGC server '%s' registered for map", ogcserver.name)
                        else:
                            _LOG.debug(
                                "Ignoring OGC server '%s', Don't match the base URL '%s' and '%s'",
                                ogcserver.name,
                                base_url,
                                url,
                            )
                    if self.ogcserver_accesscontrols and single_ogc_server is not None:
                        if os.environ.get("QGIS_PROJECT_FILE"):
                            _LOG.error(
                                "We have OGC servers with and without parameter MAP and a value in "
                                "QGIS_PROJECT_FILE, fallback to single OGC server mode."
                            )
                            self.ogcserver_accesscontrols = {}
                        else:
                            _LOG.error(
                                "We have OGC servers with and without parameter MAP but no value in "
                                "QGIS_PROJECT_FILE, fallback to multiple OGC server mode."
                            )
                            single_ogc_server = None
                    if single_ogc_server is not None:
                        self.single = True
                        self.ogcserver_accesscontrol = OGCServerAccessControl(
                            server_iface,
                            single_ogc_server.name,
                            os.environ["QGIS_PROJECT_FILE"],
                            config.get("srid"),
                            DBSession,
                            single_ogc_server,
                        )

                        _LOG.info("Use OGC server named '%s'.", single_ogc_server.name)
                    else:
                        self.single = False
                    self.initialized = True
                finally:
                    session.close()
            else:
                _LOG.error(
                    "The environment variable 'GEOMAPFISH_OGCSERVER', 'GEOMAPFISH_ACCESSCONTROL_CONFIG' "
                    "or 'GEOMAPFISH_ACCESSCONTROL_BASE_URL' should be defined.",
                )

        except Exception:  # pylint: disable=broad-except
            _LOG.exception("Cannot setup GeoMapFishAccessControl")

        server_iface.registerAccessControl(self, int(os.environ.get("GEOMAPFISH_POSITION", 100)))

    def get_ogcserver_accesscontrol_config(self) -> None:
        """Get the config."""
        if self.single:
            raise GMFException(
                "The method 'get_ogcserver_accesscontrol_config' can't be called on 'single' server"
            )

    def get_ogcserver_accesscontrol(self) -> "OGCServerAccessControl":
        """Get the OGCServerAccessControl instance."""
        parameters = self.serverInterface().requestHandler().parameterMap()

        if self.single:
            if "MAP" in parameters:
                raise GMFException("The map parameter should not be provided")
            return self.ogcserver_accesscontrol

        config_file = self.serverInterface().configFilePath()

        if config_file not in self.ogcserver_accesscontrols:
            raise GMFException(
                f"The map '{config_file}' is not found possible values: "
                f"{', '.join(self.ogcserver_accesscontrols.keys())}"
            )
        return cast("OGCServerAccessControl", self.ogcserver_accesscontrols[config_file]["access_control"])

    def layerFilterSubsetString(self, layer: QgsVectorLayer) -> str | None:  # pylint: disable=invalid-name
        """Return an additional subset string (typically SQL) filter."""
        try:
            if not self.initialized:
                _LOG.error("Call on uninitialized plugin")
                return "0"
            return self.get_ogcserver_accesscontrol().layerFilterSubsetString(layer)
        except Exception:
            _LOG.exception("Unhandled error")
            raise

    def layerFilterExpression(self, layer: QgsVectorLayer) -> str | None:  # pylint: disable=invalid-name
        """Return an additional expression filter."""
        try:
            if not self.initialized:
                _LOG.error("Call on uninitialized plugin")
                return "0"
            return self.get_ogcserver_accesscontrol().layerFilterExpression(layer)
        except Exception:
            _LOG.exception("Unhandled error")
            raise

    def layerPermissions(  # pylint: disable=invalid-name
        self, layer: QgsVectorLayer
    ) -> qgis.server.QgsAccessControlFilter.LayerPermissions:
        """Return the layer rights."""
        try:
            if not self.initialized:
                _LOG.error("Call on uninitialized plugin")
                no_rights = QgsAccessControlFilter.LayerPermissions()
                no_rights.canRead = no_rights.canInsert = no_rights.canUpdate = no_rights.canDelete = False
                return no_rights
            return self.get_ogcserver_accesscontrol().layerPermissions(layer)
        except Exception:
            _LOG.exception("Unhandled error")
            raise

    def authorizedLayerAttributes(  # pylint: disable=invalid-name
        self, layer: QgsVectorLayer, attributes: list[str]
    ) -> list[str]:
        """Return the authorized layer attributes."""
        try:
            if not self.initialized:
                _LOG.error("Call on uninitialized plugin")
                return []
            return self.get_ogcserver_accesscontrol().authorizedLayerAttributes(layer, attributes)
        except Exception:
            _LOG.exception("Unhandled error")
            raise

    def allowToEdit(self, layer: QgsVectorLayer, feature: QgsFeature) -> bool:  # pylint: disable=invalid-name
        """Are we authorize to modify the following geometry."""
        try:
            if not self.initialized:
                _LOG.error("Call on uninitialized plugin")
                return False
            return self.get_ogcserver_accesscontrol().allowToEdit(layer, feature)
        except Exception:
            _LOG.exception("Unhandled error")
            raise

    def cacheKey(self) -> str:  # pylint: disable=invalid-name
        """Get the cache key."""
        try:
            if not self.initialized:
                _LOG.error("Call on uninitialized plugin")
                return str(random.randrange(1000000))  # noqa: S311 # nosec
            return self.get_ogcserver_accesscontrol().cacheKey()
        except Exception:
            _LOG.exception("Unhandled error")
            raise


class OGCServerAccessControl(QgsAccessControlFilter):
    """Implements GeoMapFish access restriction for one project."""

    SUBSETSTRING_TYPE = ["PostgreSQL database with PostGIS extension"]

    def __init__(
        self,
        server_iface: qgis.server.QgsServerInterface,
        ogcserver_name: str,
        map_file: str,
        srid: int,
        DBSession: sessionmaker,  # pylint: disable=invalid-name
        ogcserver: Optional["main.OGCServer"] = None,
    ):
        """Initialize the plugin."""
        super().__init__(server_iface)

        self.server_iface = server_iface
        self.map_file = map_file
        self.srid = srid
        self.DBSession = DBSession  # pylint: disable=invalid-name

        self.area_cache: dict[Any, tuple[Access, BaseGeometry]] = {}
        self.layers: dict[str, list[main.LayerWMS]] | None = None
        self.lock = Lock()
        self.srid = srid
        self.ogcserver = ogcserver

        from c2cgeoportal_commons.models import (  # pylint: disable=import-outside-toplevel
            InvalidateCacheEvent,
        )

        @zope.event.classhandler.handler(InvalidateCacheEvent)
        def handle(_: InvalidateCacheEvent) -> None:
            _LOG.info("=== invalidate ===")
            self._init(ogcserver_name)

        self._init(ogcserver_name)

    def project(self) -> QgsProject:
        """Get the project."""
        return QgsConfigCache.instance().project(self.map_file)

    def _init(self, ogcserver_name: str) -> None:
        with self.lock:
            try:
                self.layers = None

                from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
                    OGCServer,
                )

                if self.ogcserver is None:
                    session = self.DBSession()
                    try:
                        self.ogcserver = (
                            session.query(OGCServer).filter(OGCServer.name == ogcserver_name).one_or_none()
                        )
                    finally:
                        session.close()
                if self.ogcserver is None:
                    _LOG.error(
                        "No OGC server found for '%s', project: '%s' => no rights",
                        ogcserver_name,
                        self.map_file,
                    )
            except Exception:  # pylint: disable=broad-except
                _LOG.exception("Cannot setup OGCServerAccessControl")

    def ogc_layer_name(self, layer: QgsVectorLayer) -> str:
        """Get the OGC layer name."""
        use_layer_id, _ = self.project().readBoolEntry("WMSUseLayerIDs", "/", False)
        if use_layer_id:
            return layer.id()
        return layer.shortName() or layer.name()

    def get_layers(self, session: Session) -> dict[str, list["main.Layer"]]:
        """
        Get the list of GMF WMS layers that can give access to each QGIS layer or group.

        That is, for each QGIS layer tree node, the list of GMF WMS layers that:
            - correspond to this ogc_server
            - contains QGIS node name in the layer_wms.layer field.
        Returns a dict with:
            key: QGIS layer tree node name
            value: list of c2cgeoportal_commons.models.main.LayerWMS instances.
        """
        if self.ogcserver is None:
            return {}

        if self.layers is not None:
            return self.layers

        with self.lock:
            from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
                LayerWMS,
                RestrictionArea,
            )

            nodes = {}  # dict { node name: list of ancestor node names }

            def browse(path: list[str], node: QgsLayerTreeNode) -> None:
                if isinstance(node, QgsLayerTreeLayer):
                    ogc_name = self.ogc_layer_name(node.layer())
                elif isinstance(node, QgsLayerTreeGroup):
                    ogc_name = node.customProperty("wmsShortName") or node.name()
                else:
                    ogc_name = node.name()

                nodes[ogc_name] = [ogc_name]

                for name in path:
                    nodes[ogc_name].append(name)

                for layer in node.children():
                    browse(path + [ogc_name], layer)

            browse([], self.project().layerTreeRoot())

            for ogc_layer_name, _ in nodes.items():
                _LOG.debug("QGIS layer: %s", ogc_layer_name)

            # Transform ancestor names in LayerWMS instances
            layers: dict[str, list[LayerWMS]] = {}
            for layer in (
                session.query(LayerWMS)
                .options(subqueryload(LayerWMS.restrictionareas).subqueryload(RestrictionArea.roles))
                .filter(LayerWMS.ogc_server_id == self.ogcserver.id)
                .all()
            ):
                # To load the metadata
                layer.get_metadata("protectedAttributes")
                found = False
                for ogc_layer_name, ancestors in nodes.items():
                    for ancestor in ancestors:
                        if ancestor in layer.layer.split(","):
                            found = True
                            _LOG.debug("GeoMapFish layer: name: %s, layer: %s", layer.name, layer.layer)
                            layers.setdefault(ogc_layer_name, []).append(layer)
                if not found:
                    _LOG.info("Rejected GeoMapFish layer: name: %s, layer: %s", layer.name, layer.layer)

            session.expunge_all()
            if _LOG.isEnabledFor(logging.DEBUG):
                messages = []
                for ogc_name, gmf_layers in layers.items():
                    messages.append(f"{ogc_name}: {', '.join([layer.name for layer in gmf_layers])}")
                _LOG.debug(
                    "layers (<OGC layer>: <GMF layers>):\n%s",
                    "\n".join(messages),
                )
            self.layers = layers
            return layers

    def get_roles(self, session: Session) -> str | list["main.Role"]:
        """
        Get the current user's available roles based on request parameter USER_ID.

        Returns:
        - List of c2cgeoportal_commons.models.main.Role instances.

        """
        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            Role,
        )

        parameters = self.serverInterface().requestHandler().parameterMap()

        if parameters.get("USER_ID") == "0":
            return "ROOT"

        if "ROLE_IDS" not in parameters:
            return []

        roles = (
            session.query(Role)
            .options(
                joinedload(Role.functionalities),
            )
            .filter(Role.id.in_(parameters.get("ROLE_IDS").split(",")))
            .all()
        )

        _LOG.debug("Roles: %s", ",".join([role.name for role in roles]) if roles else "-")
        return roles

    @staticmethod
    def get_restriction_areas(
        gmf_layers: list["main.Layer"],
        read_write: bool = False,
        roles: str | list["main.Role"] | None = None,
    ) -> tuple[Access, BaseGeometry]:
        """
        Get access areas given by GMF layers and user roles for an access mode.

        If roles is "ROOT" => full access
        If roles is None or [] => no access
        Else shapely.unary_union(result) => area of access

        Returns:
        - Access mode (NO | AREA | FULL)
        - List of access areas as shapely geometric objects

        """
        # Root...
        if roles == "ROOT":
            return Access.FULL, None

        if not read_write:
            for layer in gmf_layers:
                if layer.public:
                    return Access.FULL, None

        if not roles:
            return Access.NO, None

        from c2cgeoportal_commons.models.main import (  # pylint: disable=import-outside-toplevel
            Role,
        )

        restriction_areas = set()
        for layer in gmf_layers:
            for restriction_area in layer.restrictionareas:
                for role in roles or []:
                    assert isinstance(role, Role)  # nosec
                    restriction_area_roles_ids = [ra_role.id for ra_role in restriction_area.roles]
                    if role.id in restriction_area_roles_ids and (
                        read_write is False or restriction_area.readwrite is True
                    ):
                        if restriction_area.area is None:
                            return Access.FULL, None
                        restriction_areas.update({restriction_area})

        if not restriction_areas:
            return Access.NO, None

        return (
            Access.AREA,
            [geoalchemy2.shape.to_shape(restriction_area.area) for restriction_area in restriction_areas],
        )

    def get_area(self, layer: str, session: Session, read_write: bool = False) -> tuple[Access, BaseGeometry]:
        """
        Calculate access area for a QgsMapLayer and an access mode.

        Returns:
        - Access mode (NO | AREA | FULL)
        - Access area as WKT or None

        """
        roles = self.get_roles(session)
        if roles == "ROOT":
            return Access.FULL, None
        if not isinstance(roles, list):
            raise RuntimeError(f"Roles is not a list: {roles}")

        ogc_name = self.ogc_layer_name(layer)
        key = (ogc_name, tuple(sorted(role.id for role in roles)), read_write)

        if key in self.area_cache:
            return self.area_cache[key]

        gmf_layers = self.get_layers(session).get(ogc_name, None)
        if gmf_layers is None:
            raise Exception(  # pylint: disable=broad-exception-raised
                f"Access to an unknown layer '{ogc_name}', "
                f"from [{', '.join(self.get_layers(session).keys())}]"
            )

        access, restriction_areas = self.get_restriction_areas(gmf_layers, read_write, roles=roles)

        if access is not Access.AREA:
            self.area_cache[key] = (access, None)
            return access, None

        area = ops.unary_union(restriction_areas)
        self.area_cache[key] = (Access.AREA, area)
        return (Access.AREA, area)

    def layerFilterSubsetString(self, layer: QgsVectorLayer) -> str | None:  # pylint: disable=invalid-name
        """Get an additional subset string (typically SQL) filter."""
        _LOG.debug("layerFilterSubsetString %s %s", layer.name(), layer.dataProvider().storageType())

        if self.ogcserver is None:
            parameters = self.serverInterface().requestHandler().parameterMap()
            _LOG.warning(
                "Call on uninitialized plugin, map: %s",
                os.environ.get("QGIS_PROJECT_FILE", parameters.get("MAP")),
            )
            return "FALSE"

        try:
            if layer.dataProvider().storageType() not in self.SUBSETSTRING_TYPE:
                _LOG.debug("layerFilterSubsetString not in type")
                return None

            session = self.DBSession()
            try:
                access, area = self.get_area(layer, session)
            finally:
                session.close()
            if access is Access.FULL:
                _LOG.debug("layerFilterSubsetString no area")
                return None
            if access is Access.NO:
                _LOG.debug("layerFilterSubsetString not allowed")
                return "0"

            area = f"ST_GeomFromText('{area.wkt}', {self.srid})"
            if self.srid != layer.crs().postgisSrid():
                area = f"ST_transform({area}, {layer.crs().postgisSrid()})"
            result = (
                "ST_intersects("
                f"{QgsDataSourceUri(layer.dataProvider().dataSourceUri()).geometryColumn()}, {area})"
            )
            _LOG.debug("layerFilterSubsetString filter: %s", result)
            return result
        except Exception:
            _LOG.exception("Cannot run layerFilterSubsetString")
            raise

    def layerFilterExpression(self, layer: QgsVectorLayer) -> str | None:  # pylint: disable=invalid-name
        """Get an additional expression filter."""
        _LOG.debug("layerFilterExpression %s %s", layer.name(), layer.dataProvider().storageType())

        if self.ogcserver is None:
            parameters = self.serverInterface().requestHandler().parameterMap()
            _LOG.warning(
                "Call on uninitialized plugin, map: %s",
                os.environ.get("QGIS_PROJECT_FILE", parameters.get("MAP")),
            )
            return "FALSE"

        try:
            if layer.dataProvider().storageType() in self.SUBSETSTRING_TYPE:
                _LOG.debug("layerFilterExpression not in type")
                return None

            session = self.DBSession()
            try:
                access, area = self.get_area(layer, session)
            finally:
                session.close()
            if access is Access.FULL:
                _LOG.debug("layerFilterExpression no area")
                return None
            if access is Access.NO:
                _LOG.debug("layerFilterExpression not allowed")
                return "0"

            result = (
                f"intersects($geometry, transform(geom_from_wkt('{area.wkt}'), 'EPSG:{self.srid}', "
                f"'{layer.crs().authid()}'))"
            )

            _LOG.debug("layerFilterExpression filter: %s", result)
            return result
        except Exception:
            _LOG.exception("Cannot run layerFilterExpression")
            raise

    def layerPermissions(  # pylint: disable=invalid-name
        self, layer: QgsVectorLayer
    ) -> qgis.server.QgsAccessControlFilter.LayerPermissions:
        """Get the layer rights."""
        _LOG.debug("layerPermissions %s", layer.name())

        try:
            rights = QgsAccessControlFilter.LayerPermissions()
            rights.canRead = rights.canInsert = rights.canUpdate = rights.canDelete = False

            if self.ogcserver is None:
                parameters = self.serverInterface().requestHandler().parameterMap()
                _LOG.warning(
                    "Call on uninitialized plugin, map: %s",
                    os.environ.get("QGIS_PROJECT_FILE", parameters.get("MAP")),
                )
                return rights

            session = self.DBSession()
            try:
                roles = self.get_roles(session)

                if roles == "ROOT":
                    rights.canRead = True

                layers = self.get_layers(session)
                ogc_layer_name = self.ogc_layer_name(layer)
                if ogc_layer_name not in layers:
                    return rights
                gmf_layers = layers[ogc_layer_name]
            finally:
                session.close()
            access, _ = self.get_restriction_areas(gmf_layers, roles=roles)
            if access is not Access.NO:
                rights.canRead = True

            access, _ = self.get_restriction_areas(gmf_layers, read_write=True, roles=roles)
            rights.canInsert = rights.canUpdate = rights.canDelete = access is not Access.NO

            return rights
        except Exception:
            _LOG.exception("Cannot run layerPermissions")
            raise

    def authorizedLayerAttributes(  # pylint: disable=invalid-name
        self, layer: QgsVectorLayer, attributes: list[str]
    ) -> list[str]:
        """Get the authorized layer attributes."""
        roles = self.get_roles(self.DBSession())
        if roles == "ROOT":
            return attributes

        assert not isinstance(roles, str)  # nosec

        if self.ogcserver is None:
            parameters = self.serverInterface().requestHandler().parameterMap()
            _LOG.warning(
                "Call on uninitialized plugin, map: %s",
                os.environ.get("QGIS_PROJECT_FILE", parameters.get("MAP")),
            )
            return []

        session = self.DBSession()
        try:
            layers = self.get_layers(session)
            ogc_layer_name = self.ogc_layer_name(layer)
            if ogc_layer_name not in layers:
                return []
            gmf_layers = layers[ogc_layer_name]
            protected_attributes = []
            for gmf_layer in gmf_layers:
                for metadata in gmf_layer.get_metadata("protectedAttributes"):
                    protected_attributes.extend(metadata.value.split(","))

            allowed_attributes = [a for a in attributes if a not in protected_attributes]
            for role in roles:
                for functionality in role.functionalities:
                    if functionality.name == "allowed_attributes" and ":" in functionality.value:
                        layer_name, layer_protected_attributes = functionality.value.split(":", 1)
                        if layer_name == ogc_layer_name:
                            for protected_attribute in layer_protected_attributes.split(","):
                                if protected_attribute in attributes:
                                    allowed_attributes.append(protected_attribute)
            return allowed_attributes

        except Exception:
            _LOG.exception("Cannot run authorizedLayerAttributes")
            raise
        finally:
            session.close()

    def allowToEdit(self, layer: QgsVectorLayer, feature: QgsFeature) -> bool:  # pylint: disable=invalid-name
        """Are we authorize to modify the following geometry."""
        _LOG.debug("allowToEdit")

        if self.ogcserver is None:
            parameters = self.serverInterface().requestHandler().parameterMap()
            _LOG.warning(
                "Call on uninitialized plugin, map: %s",
                os.environ.get("QGIS_PROJECT_FILE", parameters.get("MAP")),
            )
            return False

        try:
            session = self.DBSession()
            try:
                access, area = self.get_area(layer, session, read_write=True)
            finally:
                session.close()
            if access is Access.FULL:
                _LOG.debug("layerFilterExpression no area")
                return True
            if access is Access.NO:
                _LOG.debug("layerFilterExpression not allowed")
                return False

            return area.intersects(wkb.loads(feature.geometry().asWkb().data()))
        except Exception:
            _LOG.exception("Cannot run allowToEdit")
            raise

    def cacheKey(self) -> str:  # pylint: disable=invalid-name
        """Get the cache key."""
        # Root...
        session = self.DBSession()
        try:
            roles = self.get_roles(session)
        finally:
            session.close()
        if roles == "ROOT":
            return f"{self.serverInterface().getEnv('HTTP_HOST')}-ROOT"
        if isinstance(roles, str):
            _LOG.error("Unknown values for roles: %s", roles)
            return f"{self.serverInterface().getEnv('HTTP_HOST')}-ROOT"
        return (
            f"{self.serverInterface().getEnv('HTTP_HOST')}-"
            f"{','.join(str(role.id) for role in sorted(roles, key=lambda role: role.id))}"
        )
