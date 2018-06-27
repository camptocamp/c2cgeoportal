# -*- coding: utf-8 -*-
"""
Copyright: (C) 2016 by Camptocamp SA
Contact: info@camptocamp.com

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License, or (at your
    option) any later version.
"""

from qgis.core import QgsMessageLog

import json
import os
import traceback
from shapely import ops
import geoalchemy2
import sqlalchemy

from qgis.server import QgsAccessControlFilter
from qgis.core import QgsDataSourceUri

from sqlalchemy.orm import configure_mappers
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from c2cgeoportal_commons.config import config


class GMFException(Exception):
    def __init__(self, msg):
        super(GMFException, self).__init__(msg)


class GeoMapFishAccessControl(QgsAccessControlFilter):
    """ Implements GeoMapFish access restriction """

    EXPRESSION_TYPE = ["GPKG", "PostgreSQL database with PostGIS extension"]

    def __init__(self, server_iface):
        super().__init__(server_iface)

        self.server_iface = server_iface
        self.area_cache = {}

        if "GEOMAPFISH_OGCSERVER" not in os.environ:
            raise GMFException("The environment variable 'GEOMAPFISH_OGCSERVER' is not defined.")

        self.srid = os.environ["GEOMAPFISH_SRID"]

        config.init(os.environ.get('GEOMAPFISH_CONFIG', '/etc/qgisserver/geomapfish.yaml'))
        self.config = config

        from c2cgeoportal_commons.models.main import LayerWMS, OGCServer
        configure_mappers()

        engine = sqlalchemy.create_engine(config.get('sqlalchemy_slave.url'))
        session_factory = sessionmaker()
        session_factory.configure(bind=engine)
        self.DBSession = scoped_session(session_factory)

        self.ogcserver = self.DBSession.query(OGCServer) \
            .filter(OGCServer.name == os.environ["GEOMAPFISH_OGCSERVER"]) \
            .one()

        self.layers = {}
        # TODO manage groups ...
        for layer in self.DBSession.query(LayerWMS).filter(LayerWMS.ogc_server_id == self.ogcserver.id).all():
            for name in layer.layer.split(','):
                if name not in self.layers:
                    self.layers[name] = []
                self.layers[name].append(layer)
        QgsMessageLog.logMessage('[accesscontrol] layers: {}'.format(
            json.dumps(self.layers, sort_keys=True, indent=4)
        ))

        server_iface.registerAccessControl(self, int(os.environ.get("GEOMAPFISH_POSITION", 100)))

    def get_role(self):
        from c2cgeoportal_commons.models.main import Role
        parameters = self.serverInterface().requestHandler().parameterMap()
        return self.DBSession.query(Role).get(parameters['ROLE_ID'])

    def get_restriction_areas(self, gmf_layers, rw=False, role=False):
        """
        None => full access
        [] => no access
        shapely.ops.cascaded_union(result) => geom of access
        """
        if role is False:
            role = self.get_role()

        restriction_areas = []
        for layer in gmf_layers:
            for restriction_area in layer.restrictionareas:
                if role in restriction_area.roles and rw is False or restriction_area.readwrite is True:
                    if restriction_area.area is None:
                        return None
                    else:
                        restriction_areas.append(geoalchemy2.shape.to_shape(
                            restriction_area.area
                        ))

        return restriction_areas

    def get_area(self, layer, rw=False):
        role = self.get_role()
        key = (layer.name(), role.name, rw)

        if key in self.area_cache:
            return self.area_cache[key]

        gmf_layers = self.layers[layer.name()]
        restriction_areas = self.get_restriction_areas(gmf_layers, role=role)

        if restriction_areas is None:
            self.area_cache[key] = None
            return None

        area = ops.unary_union(restriction_areas).wkt
        self.area_cache[key] = area
        return area

    def layerFilterSubsetString(self, layer):  # NOQA
        """ Return an additional subset string (typically SQL) filter """
        QgsMessageLog.logMessage("layerFilterSubsetString {}".format(layer.dataProvider().storageType()))

        try:
            if layer.dataProvider().storageType() not in self.EXPRESSION_TYPE:
                return None

            area = self.get_area(layer)
            if area is None:
                return None
            area = "ST_GeomFromText('{}', {})".format(
                area, self.srid
            )
            if self.srid != layer.crs().postgisSrid():
                area = "ST_transform({}, {})".format(
                    area, layer.crs().postgisSrid()
                )
            QgsMessageLog.logMessage("ST_intersects({}, {})".format(
                QgsDataSourceUri(layer.dataProvider().dataSourceUri()).geometryColumn(), area
            ))
            return "ST_intersects({}, {})".format(
                QgsDataSourceUri(layer.dataProvider().dataSourceUri()).geometryColumn(), area
            )
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc())
            raise

    def layerFilterExpression(self, layer):  # NOQA
        """ Return an additional expression filter """
        QgsMessageLog.logMessage("layerFilterExpression {}".format(layer.dataProvider().storageType()))

        try:
            if layer.dataProvider().storageType() in self.EXPRESSION_TYPE:
                return None

            area = self.get_area(layer)

            if area is None:
                return None

            QgsMessageLog.logMessage("intersects($geometry, geom_from_wkt('{}'))".format(area))
            #return "geometry = '{}'".format(ops.unary_union(restriction_areas).wkt)
            #return "fid = 2"
            # TODO cache the union
            # TODO verify the geometry
            return "intersects($geometry, transform(geom_from_wkt('{}'), 'EPSG:{}', 'EPSG:{}')".format(
                area, self.srid, layer.crs().projectionAcronym()
            )
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc())
            raise

    def layerPermissions(self, layer):  # NOQA
        """ Return the layer rights """
        QgsMessageLog.logMessage("layerPermissions {}".format(layer.name()))

        try:
            rights = QgsAccessControlFilter.LayerPermissions()
            rights.canRead = rights.canInsert = rights.canUpdate = rights.canDelete = False

            if layer.name() not in self.layers:
                return rights

            gmf_layers = self.layers[layer.name()]
            for l in gmf_layers:
                if l.public is True:
                    rights.canRead = True

            if not rights.canRead:
                role = self.get_role()
                restriction_areas = self.get_restriction_areas(gmf_layers, role=role)
                if restriction_areas is not None and len(restriction_areas) == 0:
                    return rights
                rights.canRead = True

            restriction_areas = self.get_restriction_areas(gmf_layers, rw=True, role=role)
            rights.canInsert = rights.canUpdate = rights.canDelete = \
                restriction_areas is None or len(restriction_areas) > 0

            return rights
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc())
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

        try:
            area = self.get_area(layer, rw=True)

            return area is None or area.intersect(feature.geom)
        except Exception:
            QgsMessageLog.logMessage(traceback.format_exc())
            raise

    def cacheKey(self):  # NOQA
        return "{}-{}".format(
            self.serverInterface().requestHandler().parameter("Host"),
            self.get_role().name,
        )
