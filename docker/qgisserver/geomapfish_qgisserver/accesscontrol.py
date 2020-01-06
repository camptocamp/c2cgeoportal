# -*- coding: utf-8 -*-
"""
Copyright: (C) 2016-2019 by Camptocamp SA
Contact: info@camptocamp.com

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License, or (at your
    option) any later version.
"""


from enum import Enum
import json
import os
import re
import sys
from threading import Lock
import traceback

from c2c.template.config import config
import c2cwsgiutils.broadcast
import geoalchemy2
from qgis.core import Qgis, QgsDataSourceUri, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsMessageLog, QgsProject
from qgis.server import QgsAccessControlFilter
from shapely import ops
import sqlalchemy
from sqlalchemy.orm import configure_mappers, scoped_session, sessionmaker
import yaml
import zope.event.classhandler


class GMFException(Exception):
    pass


class Access(Enum):
    NO = 1
    AREA = 2
    FULL = 3


class GeoMapFishAccessControl(QgsAccessControlFilter):
    def __init__(self, server_iface):
        super().__init__(server_iface)

        self.server_iface = server_iface
        self.initialized = False

        try:
            config.init(os.environ.get("GEOMAPFISH_CONFIG", "/etc/qgisserver/geomapfish.yaml"))

            c2cwsgiutils.broadcast.init()

            configure_mappers()
            db_match = re.match(".*(@[^@]+)$", config.get("sqlalchemy_slave.url"))
            QgsMessageLog.logMessage(
                "Connect to the database: ***{}".format(db_match.group(1) if db_match else ""),
                "GeoMapFishAccessControl",
                level=Qgis.Info,
            )
            engine = sqlalchemy.create_engine(
                config["sqlalchemy_slave.url"], **(config.get_config().get("sqlalchemy", {}))
            )
            session_factory = sessionmaker()
            session_factory.configure(bind=engine)
            DBSession = scoped_session(session_factory)  # noqa: N806

            if "GEOMAPFISH_OGCSERVER" in os.environ:
                self.single = True
                self.ogcserver_accesscontrol = OGCServerAccessControl(
                    server_iface, os.environ["GEOMAPFISH_OGCSERVER"], config.get("srid"), DBSession
                )

                QgsMessageLog.logMessage(
                    "Use OGC server named '{}'.".format(os.environ["GEOMAPFISH_OGCSERVER"]),
                    "GeoMapFishAccessControl",
                    level=Qgis.Info,
                )
                self.initialized = True
            elif "GEOMAPFISH_ACCESSCONTROL_CONFIG" in os.environ:
                self.single = False
                self.ogcserver_accesscontrols = {}
                with open(os.environ["GEOMAPFISH_ACCESSCONTROL_CONFIG"]) as ac_config_file:
                    ac_config = yaml.safe_load(ac_config_file.read())

                for map_, map_config in ac_config.get("map_config").items():
                    map_config["access_control"] = OGCServerAccessControl(
                        server_iface, map_config["ogc_server"], config.get("srid"), DBSession
                    )
                    self.ogcserver_accesscontrols[map_] = map_config
                QgsMessageLog.logMessage(
                    "Use config '{}'.".format(os.environ["GEOMAPFISH_ACCESSCONTROL_CONFIG"]),
                    "GeoMapFishAccessControl",
                    level=Qgis.Info,
                )
                self.initialized = True
            else:
                QgsMessageLog.logMessage(
                    "The environment variable 'GEOMAPFISH_OGCSERVER' or "
                    "'GEOMAPFISH_ACCESSCONTROL_CONFIG' is not defined.",
                    "GeoMapFishAccessControl",
                    level=Qgis.Critical,
                )

        except Exception:
            print("".join(traceback.format_exception(*sys.exc_info())))
            QgsMessageLog.logMessage(
                "".join(traceback.format_exception(*sys.exc_info())),
                "GeoMapFishAccessControl",
                level=Qgis.Critical,
            )

        server_iface.registerAccessControl(self, int(os.environ.get("GEOMAPFISH_POSITION", 100)))

    def get_ogcserver_accesscontrol_config(self):
        if self.single:
            raise GMFException(
                "The method 'get_ogcserver_accesscontrol_config' can't be called on 'single' server"
            )

    def get_ogcserver_accesscontrol(self):
        if self.single:
            return self.ogcserver_accesscontrol
        parameters = self.serverInterface().requestHandler().parameterMap()
        return self.ogcserver_accesscontrols[parameters["MAP"]]["access_control"]

    def layerFilterSubsetString(self, layer):  # NOQA
        """ Return an additional subset string (typically SQL) filter """
        if not self.initialized:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            return "0"
        return self.get_ogcserver_accesscontrol().layerFilterSubsetString(layer)

    def layerFilterExpression(self, layer):  # NOQA
        """ Return an additional expression filter """
        if not self.initialized:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            return "0"
        return self.get_ogcserver_accesscontrol().layerFilterExpression(layer)

    def layerPermissions(self, layer):  # NOQA
        """ Return the layer rights """
        if not self.initialized:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            no_rights = QgsAccessControlFilter.LayerPermissions()
            no_rights.canRead = no_rights.canInsert = no_rights.canUpdate = no_rights.canDelete = False
            return no_rights
        return self.get_ogcserver_accesscontrol().layerPermissions(layer)

    def authorizedLayerAttributes(self, layer, attributes):  # NOQA
        """ Return the authorised layer attributes """
        if not self.initialized:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            return []
        return self.get_ogcserver_accesscontrol().authorizedLayerAttributes(layer, attributes)

    def allowToEdit(self, layer, feature):  # NOQA
        """ Are we authorise to modify the following geometry """
        if not self.initialized:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            return False
        return self.get_ogcserver_accesscontrol().allowToEdit(layer, feature)

    def cacheKey(self):  # NOQA
        return self.get_ogcserver_accesscontrol().cacheKey()


class OGCServerAccessControl(QgsAccessControlFilter):
    """ Implements GeoMapFish access restriction """

    SUBSETSTRING_TYPE = ["PostgreSQL database with PostGIS extension"]

    def __init__(self, server_iface, ogcserver_name, srid, DBSession):  # noqa: N803
        super().__init__(server_iface)

        self.server_iface = server_iface
        self.DBSession = DBSession
        self.area_cache = {}
        self.layers = None
        self.lock = Lock()
        self.project = None
        self.srid = srid
        self.ogcserver = None

        try:
            from c2cgeoportal_commons.models import InvalidateCacheEvent

            @zope.event.classhandler.handler(InvalidateCacheEvent)
            def handle(event: InvalidateCacheEvent):  # pylint: disable=unused-variable
                del event
                QgsMessageLog.logMessage("=== invalidate ===", "GeoMapFishAccessControl", level=Qgis.Info)
                with self.lock:
                    self.layers = None

            from c2cgeoportal_commons.models.main import OGCServer

            self.ogcserver = self.DBSession.query(OGCServer).filter(OGCServer.name == ogcserver_name).one()

        except Exception:
            QgsMessageLog.logMessage(
                "".join(traceback.format_exception(*sys.exc_info())),
                "GeoMapFishAccessControl",
                level=Qgis.Critical,
            )

    @staticmethod
    def ogc_layer_name(layer):
        use_layer_id, _ = QgsProject.instance().readBoolEntry("WMSUseLayerIDs", "/", False)
        if use_layer_id:
            return layer.id()
        return layer.shortName() or layer.name()

    def get_layers(self):
        """
        Get the list of GMF WMS layers that can give access to each QGIS layer or group.
        That is, for each QGIS layer tree node, the list of GMF WMS layers that:
            - correspond to this ogc_server
            - contains QGIS node name in the layer_wms.layer field.
        Returns a dict with:
            key: QGIS layer tree node name
            value: list of c2cgeoportal_commons.models.main.LayerWMS instances.
        """
        with self.lock:
            from c2cgeoportal_commons.models.main import LayerWMS

            if self.layers is not None and self.project == QgsProject.instance():
                return self.layers

            self.project = QgsProject.instance()

            nodes = {}  # dict { node name : list of ancestor node names }

            def browse(path, node):
                if isinstance(node, QgsLayerTreeLayer):
                    ogc_name = self.ogc_layer_name(node.layer())
                elif isinstance(node, QgsLayerTreeGroup):
                    ogc_name = node.customProperty("wmsShortName") or node.name()
                else:
                    ogc_name = node.name()

                nodes[ogc_name] = [ogc_name]

                for name in path:
                    nodes[ogc_name].append(name)

                for l in node.children():
                    browse(path + [ogc_name], l)

            browse([], self.project.layerTreeRoot())

            # Transform ancestor names in LayerWMS instances
            layers = {}  # dict( node name : list of LayerWMS }
            for layer in (
                self.DBSession.query(LayerWMS).filter(LayerWMS.ogc_server_id == self.ogcserver.id).all()
            ):
                for ogc_layer_name, ancestors in nodes.items():
                    for ancestor in ancestors:
                        if ancestor in layer.layer.split(","):
                            layers.setdefault(ogc_layer_name, []).append(layer)
            QgsMessageLog.logMessage(
                "[accesscontrol] layers:\n{}".format(
                    json.dumps({k: [l.name for l in v] for k, v in layers.items()}, sort_keys=True, indent=4)
                ),
                "GeoMapFishAccessControl",
                level=Qgis.Info,
            )
            self.layers = layers
            return layers

    def get_roles(self):
        """
        Get the current user's available roles based on request parameter USER_ID.
        Returns:
        - List of c2cgeoportal_commons.models.main.Role instances.
        """
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User

        parameters = self.serverInterface().requestHandler().parameterMap()

        if parameters.get("USER_ID") == "0":
            return "ROOT"

        roles = self.DBSession.query(Role).join(Role.users).filter(User.id == parameters.get("USER_ID")).all()

        QgsMessageLog.logMessage(
            "Roles: {}".format(",".join([role.name for role in roles]) if roles else "-"),
            "GeoMapFishAccessControl",
            level=Qgis.Info,
        )
        return roles

    @staticmethod
    def get_restriction_areas(gmf_layers, rw=False, roles=None):
        """
        Get access areas given by GMF layers and user roles for an access mode.

        If roles is "ROOT" => full access
        If roles is None or [] => no access
        Else shapely.ops.cascaded_union(result) => area of access

        Returns:
        - Access mode (NO | AREA | FULL)
        - List of access areas as shapely geometric objects
        """

        # Root...
        if roles == "ROOT":
            return Access.FULL, None

        if not rw:
            for l in gmf_layers:
                if l.public:
                    return Access.FULL, None

        if not roles:
            return Access.NO, None

        restriction_areas = set()
        for layer in gmf_layers:
            for restriction_area in layer.restrictionareas:
                for role in roles or []:
                    if role in restriction_area.roles and (rw is False or restriction_area.readwrite is True):
                        if restriction_area.area is None:
                            return Access.FULL, None
                        restriction_areas.update({restriction_area})

        if not restriction_areas:
            return Access.NO, None

        return (
            Access.AREA,
            [geoalchemy2.shape.to_shape(restriction_area.area) for restriction_area in restriction_areas],
        )

    def get_area(self, layer, rw=False):
        """
        Calculate access area for a QgsMapLayer and an access mode.
        Returns:
        - Access mode (NO | AREA | FULL)
        - Access area as WKT or None
        """
        roles = self.get_roles()
        if roles == "ROOT":
            return Access.FULL, None

        ogc_name = self.ogc_layer_name(layer)
        key = (ogc_name, tuple(sorted(role.id for role in roles)), rw)

        if key in self.area_cache:
            return self.area_cache[key]

        gmf_layers = self.get_layers().get(ogc_name, None)
        if gmf_layers is None:
            raise Exception("Access to an unknown layer")

        access, restriction_areas = self.get_restriction_areas(gmf_layers, rw, roles=roles)

        if access is not Access.AREA:
            self.area_cache[key] = (access, None)
            return access, None

        area = ops.unary_union(restriction_areas).wkt
        self.area_cache[key] = (Access.AREA, area)
        return (Access.AREA, area)

    def layerFilterSubsetString(self, layer):  # NOQA
        """ Returns an additional subset string (typically SQL) filter """
        if self.ogcserver is None:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            return "0"

        QgsMessageLog.logMessage(
            "layerFilterSubsetString {} {}".format(layer.name(), layer.dataProvider().storageType()),
            "GeoMapFishAccessControl",
            level=Qgis.Info,
        )

        try:
            if layer.dataProvider().storageType() not in self.SUBSETSTRING_TYPE:
                QgsMessageLog.logMessage(
                    "layerFilterSubsetString not in type", "GeoMapFishAccessControl", level=Qgis.Info
                )
                return None

            access, area = self.get_area(layer)
            if access is Access.FULL:
                QgsMessageLog.logMessage(
                    "layerFilterSubsetString no area", "GeoMapFishAccessControl", level=Qgis.Info
                )
                return None
            if access is Access.NO:
                QgsMessageLog.logMessage(
                    "layerFilterSubsetString not allowed", "GeoMapFishAccessControl", level=Qgis.Info
                )
                return "0"

            area = "ST_GeomFromText('{}', {})".format(area, self.srid)
            if self.srid != layer.crs().postgisSrid():
                area = "ST_transform({}, {})".format(area, layer.crs().postgisSrid())
            result = "ST_intersects({}, {})".format(
                QgsDataSourceUri(layer.dataProvider().dataSourceUri()).geometryColumn(), area
            )
            QgsMessageLog.logMessage(
                "layerFilterSubsetString filter: {}".format(result),
                "GeoMapFishAccessControl",
                level=Qgis.Info,
            )
            return result
        except Exception:
            QgsMessageLog.logMessage(
                "".join(traceback.format_exception(*sys.exc_info())),
                "GeoMapFishAccessControl",
                level=Qgis.Critical,
            )
            raise

    def layerFilterExpression(self, layer):  # NOQA
        """ Returns an additional expression filter """
        if self.ogcserver is None:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            return "0"

        QgsMessageLog.logMessage(
            "layerFilterExpression {} {}".format(layer.name(), layer.dataProvider().storageType()),
            "GeoMapFishAccessControl",
            level=Qgis.Info,
        )

        try:
            if layer.dataProvider().storageType() in self.SUBSETSTRING_TYPE:
                QgsMessageLog.logMessage(
                    "layerFilterExpression not in type", "GeoMapFishAccessControl", level=Qgis.Info
                )
                return None

            access, area = self.get_area(layer)
            if access is Access.FULL:
                QgsMessageLog.logMessage(
                    "layerFilterExpression no area", "GeoMapFishAccessControl", level=Qgis.Info
                )
                return None
            if access is Access.NO:
                QgsMessageLog.logMessage(
                    "layerFilterExpression not allowed", "GeoMapFishAccessControl", level=Qgis.Info
                )
                return "0"

            result = "intersects($geometry, transform(geom_from_wkt('{}'), 'EPSG:{}', '{}'))".format(
                area, self.srid, layer.crs().authid()
            )
            QgsMessageLog.logMessage(
                "layerFilterExpression filter: {}".format(result), "GeoMapFishAccessControl", level=Qgis.Info
            )
            return result
        except Exception:
            QgsMessageLog.logMessage(
                "".join(traceback.format_exception(*sys.exc_info())),
                "GeoMapFishAccessControl",
                level=Qgis.Critical,
            )
            raise

    def layerPermissions(self, layer):  # NOQA
        """ Returns the layer rights """
        QgsMessageLog.logMessage(
            "layerPermissions {}".format(layer.name()), "GeoMapFishAccessControl", level=Qgis.Info
        )

        try:
            rights = QgsAccessControlFilter.LayerPermissions()
            rights.canRead = rights.canInsert = rights.canUpdate = rights.canDelete = False

            if self.ogcserver is None:
                QgsMessageLog.logMessage(
                    "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
                )
                return rights

            layers = self.get_layers()
            ogc_layer_name = self.ogc_layer_name(layer)
            if ogc_layer_name not in layers:
                return rights
            gmf_layers = self.get_layers()[ogc_layer_name]

            roles = self.get_roles()
            access, _ = self.get_restriction_areas(gmf_layers, roles=roles)
            if access is not Access.NO:
                rights.canRead = True

            access, _ = self.get_restriction_areas(gmf_layers, rw=True, roles=roles)
            rights.canInsert = rights.canUpdate = rights.canDelete = access is not Access.NO

            return rights
        except Exception:
            QgsMessageLog.logMessage(
                "".join(traceback.format_exception(*sys.exc_info())),
                "GeoMapFishAccessControl",
                level=Qgis.Critical,
            )
            raise

    def authorizedLayerAttributes(self, layer, attributes):  # NOQA
        """ Returns the authorised layer attributes """
        del layer

        if self.ogcserver is None:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            return []

        # TODO
        return attributes

    def allowToEdit(self, layer, feature):  # NOQA
        """ Are we authorise to modify the following geometry """
        QgsMessageLog.logMessage("allowToEdit")

        if self.ogcserver is None:
            QgsMessageLog.logMessage(
                "Call on uninitialized plugin", "GeoMapFishAccessControl", level=Qgis.Critical
            )
            return False

        try:
            access, area = self.get_area(layer, rw=True)
            if access is Access.FULL:
                QgsMessageLog.logMessage("layerFilterExpression no area")
                return True
            if access is Access.NO:
                QgsMessageLog.logMessage("layerFilterExpression not allowed")
                return False

            return area.intersect(feature.geom)
        except Exception:
            QgsMessageLog.logMessage("".join(traceback.format_exception(*sys.exc_info())))
            raise

    def cacheKey(self):  # NOQA
        # Root...
        roles = self.get_roles()
        if roles == "ROOT":
            return "{}-{}".format(self.serverInterface().requestHandler().parameter("Host"), -1)
        return "{}-{}".format(
            self.serverInterface().requestHandler().parameter("Host"),
            ",".join(str(role.id) for role in sorted(roles, key=lambda role: role.id)),
        )
