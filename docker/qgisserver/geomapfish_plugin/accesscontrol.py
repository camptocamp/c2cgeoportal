# -*- coding: utf-8 -*-
"""
Copyright: (C) 2016-2018 by Camptocamp SA
Contact: info@camptocamp.com

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License, or (at your
    option) any later version.
"""


import c2cwsgiutils.broadcast
import geoalchemy2
import json
import os
import sqlalchemy
import sys
import traceback
import yaml
import zope.event.classhandler

from c2cgeoportal_commons.config import config
from enum import Enum
from qgis.core import QgsMessageLog, QgsDataSourceUri, QgsProject
from qgis.server import QgsAccessControlFilter
from shapely import ops
from sqlalchemy.orm import configure_mappers, scoped_session, sessionmaker
from threading import Lock


class GMFException(Exception):
    def __init__(self, msg):
        super(GMFException, self).__init__(msg)


class Access(Enum):
    NO = 1
    AREA = 2
    FULL = 3


class GeoMapFishAccessControl(QgsAccessControlFilter):

    def __init__(self, server_iface):
        super().__init__(server_iface)

        self.server_iface = server_iface

        try:
            config.init(os.environ.get('GEOMAPFISH_CONFIG', '/etc/qgisserver/geomapfish.yaml'))
            self.srid = config.get('srid')

            c2cwsgiutils.broadcast.init(None)

            configure_mappers()
            engine = sqlalchemy.create_engine(config.get('sqlalchemy_slave.url'))
            session_factory = sessionmaker()
            session_factory.configure(bind=engine)
            DBSession = scoped_session(session_factory)  # noqa: N806

            if "GEOMAPFISH_OGCSERVER" in os.environ:
                self.single = True
                self.ogcserver_accesscontrol = OGCServerAccessControl(
                    server_iface, os.environ['GEOMAPFISH_OGCSERVER'], DBSession
                )

                QgsMessageLog.logMessage("Use OGC server named '{}'.".format(
                    os.environ["GEOMAPFISH_OGCSERVER"]
                ))
            elif "GEOMAPFISH_ACCESSCONTROL_CONFIG" in os.environ:
                self.single = False
                self.ogcserver_accesscontrols = {}
                with open(os.environ["GEOMAPFISH_ACCESSCONTROL_CONFIG"]) as ac_config_file:
                    ac_config = yaml.load(ac_config_file.read())

                for map, map_config in ac_config.get("map_config").items():
                    map_config["access_control"] = OGCServerAccessControl(
                        server_iface, map_config["ogc_server"], DBSession
                    )
                    self.ogcserver_accesscontrols[map] = map_config
                QgsMessageLog.logMessage("Use config '{}'.".format(
                    os.environ["GEOMAPFISH_ACCESSCONTROL_CONFIG"]
                ))
            else:
                raise GMFException(
                    "The environment variable 'GEOMAPFISH_OGCSERVER' or "
                    "'GEOMAPFISH_ACCESSCONTROL_CONFIG' is not defined."
                )

        except Exception:
            QgsMessageLog.logMessage(''.join(traceback.format_exception(*sys.exc_info())))
            raise

        server_iface.registerAccessControl(self, int(os.environ.get("GEOMAPFISH_POSITION", 100)))

    def get_ogcserver_accesscontrol_config(self):
        if self.single:
            raise GMFException(
                "The method 'get_ogcserver_accesscontrol_config' can't be called on 'single' server"
            )

    def get_ogcserver_accesscontrol(self):
        if self.single:
            return self.ogcserver_accesscontrol
        else:
            parameters = self.serverInterface().requestHandler().parameterMap()
            return self.ogcserver_accesscontrols[parameters["MAP"]]["access_control"]

    def layerFilterSubsetString(self, layer):  # NOQA
        """ Return an additional subset string (typically SQL) filter """
        return self.get_ogcserver_accesscontrol().layerFilterSubsetString(layer)

    def layerFilterExpression(self, layer):  # NOQA
        """ Return an additional expression filter """
        return self.get_ogcserver_accesscontrol().layerFilterExpression(layer)

    def layerPermissions(self, layer):  # NOQA
        """ Return the layer rights """
        return self.get_ogcserver_accesscontrol().layerPermissions(layer)

    def authorizedLayerAttributes(self, layer, attributes):  # NOQA
        """ Return the authorised layer attributes """
        return self.get_ogcserver_accesscontrol().layauthorizedLayerAttributeserPermissions(layer, attributes)

    def allowToEdit(self, layer, feature):  # NOQA
        """ Are we authorise to modify the following geometry """
        return self.get_ogcserver_accesscontrol().allowToEdit(layer, feature)

    def cacheKey(self):  # NOQA
        return self.get_ogcserver_accesscontrol().cacheKey()


class OGCServerAccessControl(QgsAccessControlFilter):
    """ Implements GeoMapFish access restriction """

    SUBSETSTRING_TYPE = ["GPKG", "PostgreSQL database with PostGIS extension"]

    def __init__(self, server_iface, ogcserver_name, DBSession):  # noqa: N803
        super().__init__(server_iface)

        self.server_iface = server_iface
        self.DBSession = DBSession
        self.area_cache = {}
        self.layers = None
        self.lock = Lock()
        self.project = None

        try:
            from c2cgeoportal_commons.models.main import InvalidateCacheEvent

            @zope.event.classhandler.handler(InvalidateCacheEvent)
            def handle(event: InvalidateCacheEvent):
                del event
                QgsMessageLog.logMessage("=== invalidate ===")
                with self.lock:
                    self.layers = None

            from c2cgeoportal_commons.models.main import OGCServer

            self.ogcserver = self.DBSession.query(OGCServer) \
                .filter(OGCServer.name == ogcserver_name) \
                .one()

        except Exception:
            QgsMessageLog.logMessage(''.join(traceback.format_exception(*sys.exc_info())))
            raise

    def get_layers(self):
        with self.lock:
            from c2cgeoportal_commons.models.main import LayerWMS

            if self.layers is not None and self.project == QgsProject.instance():
                return self.layers

            self.project = QgsProject.instance()

            groups = {}

            def browse(names, layer):
                groups[layer.name()] = [layer.name()]

                for name in names:
                    groups[name].append(layer.name())

                new_names = list(names)
                new_names.append(layer.name())
                for l in layer.children():
                    browse(new_names, l)

            browse([], self.project.layerTreeRoot())

            layers = {}
            for layer in self.DBSession.query(LayerWMS) \
                    .filter(LayerWMS.ogc_server_id == self.ogcserver.id).all():
                for group in layer.layer.split(','):
                    for name in groups.get(group, []):
                        layers.setdefault(name, []).append(layer)
            QgsMessageLog.logMessage('[accesscontrol] layers:\n{}'.format(
                json.dumps(
                    dict([(k, [l.name for l in v]) for k, v in layers.items()]),
                    sort_keys=True, indent=4
                )
            ))
            self.layers = layers
            return layers

    def assert_plugin_initialised(self):
        if self.ogcserver is None:
            raise Exception("The plugin is not correctly initialised")

    def get_role(self):
        from c2cgeoportal_commons.models.main import Role

        parameters = self.serverInterface().requestHandler().parameterMap()

        if parameters.get('ROLE_ID') == "0" and parameters.get('USER_ID') == "0":
            return "ROOT"

        role = self.DBSession.query(Role).get(parameters['ROLE_ID']) if 'ROLE_ID' in parameters else None
        QgsMessageLog.logMessage("Role: {}".format(role.name if role else '-'))
        return role

    @staticmethod
    def get_restriction_areas(gmf_layers, rw=False, role=None):
        """
        None => full access
        [] => no access
        shapely.ops.cascaded_union(result) => geom of access
        """

        # Root...
        if role == "ROOT":
            return Access.FULL, None

        if not rw:
            for l in gmf_layers:
                if l.public:
                    return Access.FULL, None

        if role is None:
            return Access.NO, None

        restriction_areas = []
        for layer in gmf_layers:
            for restriction_area in layer.restrictionareas:
                if role in restriction_area.roles and rw is False or restriction_area.readwrite is True:
                    if restriction_area.area is None:
                        return Access.FULL, None
                    else:
                        restriction_areas.append(geoalchemy2.shape.to_shape(restriction_area.area))

        if len(restriction_areas) == 0:
            return Access.NO, None

        return Access.AREA, restriction_areas

    def get_area(self, layer, rw=False):
        role = self.get_role()
        key = (layer.name(), role.name if role is not None else None, rw)

        if key in self.area_cache:
            return self.area_cache[key]

        if layer.name() not in self.get_layers():
            raise Exception("Access to an unknown layer")

        gmf_layers = self.get_layers()[layer.name()]
        access, restriction_areas = self.get_restriction_areas(gmf_layers, role=role)

        if access is not Access.AREA:
            self.area_cache[key] = (access, None)
            return access, None

        area = ops.unary_union(restriction_areas).wkt
        self.area_cache[key] = (Access.AREA, area)
        return (Access.AREA, area)

    def layerFilterSubsetString(self, layer):  # NOQA
        """ Return an additional subset string (typically SQL) filter """
        QgsMessageLog.logMessage("layerFilterSubsetString {} {}".format(
            layer.name(), layer.dataProvider().storageType())
        )

        self.assert_plugin_initialised()

        try:
            if layer.dataProvider().storageType() not in self.SUBSETSTRING_TYPE:
                QgsMessageLog.logMessage("layerFilterSubsetString not in type")
                return None

            access, area = self.get_area(layer)
            if access is Access.FULL:
                QgsMessageLog.logMessage("layerFilterSubsetString no area")
                return None
            elif access is Access.NO:
                QgsMessageLog.logMessage("layerFilterSubsetString not allowed")
                return "0"

            area = "ST_GeomFromText('{}', {})".format(
                area, self.srid
            )
            if self.srid != layer.crs().postgisSrid():
                area = "ST_transform({}, {})".format(
                    area, layer.crs().postgisSrid()
                )
            result = "ST_intersects({}, {})".format(
                QgsDataSourceUri(layer.dataProvider().dataSourceUri()).geometryColumn(), area
            )
            QgsMessageLog.logMessage("layerFilterSubsetString filter: {}".format(result))
            return result
        except Exception:
            QgsMessageLog.logMessage(''.join(traceback.format_exception(*sys.exc_info())))
            raise

    def layerFilterExpression(self, layer):  # NOQA
        """ Return an additional expression filter """
        QgsMessageLog.logMessage("layerFilterExpression {} {}".format(
            layer.name(), layer.dataProvider().storageType()
        ))

        self.assert_plugin_initialised()

        try:
            # Actually layerFilterSubsetString don't works on groups
            # if layer.dataProvider().storageType() in self.SUBSETSTRING_TYPE:
            #     QgsMessageLog.logMessage("layerFilterExpression not in type")
            #     return None

            access, area = self.get_area(layer)
            if access is Access.FULL:
                QgsMessageLog.logMessage("layerFilterExpression no area")
                return None
            elif access is Access.NO:
                QgsMessageLog.logMessage("layerFilterExpression not allowed")
                return "0"

            result = "intersects($geometry, transform(geom_from_wkt('{}'), 'EPSG:{}', '{}'))".format(
                area, self.srid, layer.crs().authid()
            )
            QgsMessageLog.logMessage("layerFilterExpression filter: {}".format(result))
            return result
        except Exception:
            QgsMessageLog.logMessage(''.join(traceback.format_exception(*sys.exc_info())))
            raise

    def layerPermissions(self, layer):  # NOQA
        """ Return the layer rights """
        QgsMessageLog.logMessage("layerPermissions {}".format(layer.name()))

        self.assert_plugin_initialised()

        try:
            rights = QgsAccessControlFilter.LayerPermissions()
            rights.canRead = rights.canInsert = rights.canUpdate = rights.canDelete = False

            if layer.name() not in self.get_layers():
                return rights

            gmf_layers = self.get_layers()[layer.name()]

            role = self.get_role()
            access, _ = self.get_restriction_areas(gmf_layers, role=role)
            if access is not Access.NO:
                rights.canRead = True

            access, _ = self.get_restriction_areas(gmf_layers, rw=True, role=role)
            rights.canInsert = rights.canUpdate = rights.canDelete = access is not Access.NO

            return rights
        except Exception:
            QgsMessageLog.logMessage(''.join(traceback.format_exception(*sys.exc_info())))
            raise

    @staticmethod
    def authorizedLayerAttributes(layer, attributes):  # NOQA
        """ Return the authorised layer attributes """

        del layer

        # TODO
        return attributes

    def allowToEdit(self, layer, feature):  # NOQA
        """ Are we authorise to modify the following geometry """
        QgsMessageLog.logMessage("allowToEdit")

        self.assert_plugin_initialised()

        try:
            access, area = self.get_area(layer, rw=True)
            if access is Access.FULL:
                QgsMessageLog.logMessage("layerFilterExpression no area")
                return True
            elif access is Access.NO:
                QgsMessageLog.logMessage("layerFilterExpression not allowed")
                return False

            return area.intersect(feature.geom)
        except Exception:
            QgsMessageLog.logMessage(''.join(traceback.format_exception(*sys.exc_info())))
            raise

    def cacheKey(self):  # NOQA
        # Root...
        role = self.get_role()
        if role == "ROOT":
            return "{}-{}".format(
                self.serverInterface().requestHandler().parameter("Host"), -1
            )
        return "{}-{}".format(
            self.serverInterface().requestHandler().parameter("Host"),
            role.id if role is not None else '',
        )
