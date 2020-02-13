# -*- coding: utf-8 -*-
"""
Copyright: (C) 2016-2019 by Camptocamp SA
Contact: info@camptocamp.com

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by the
    Free Software Foundation; either version 2 of the License, or (at your
    option) any later version.
"""

import os
from unittest.mock import Mock, patch

import pytest
from geoalchemy2.shape import from_shape
from qgis.core import QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer
from qgis.server import QgsServerInterface
from shapely.geometry import LineString, box, shape

from geomapfish_qgisserver.accesscontrol import Access, GeoMapFishAccessControl, OGCServerAccessControl
from .accesscontrol_test import add_node_in_qgis_project, set_request_parameters


area1 = box(400000, 70000, 800000, 100000)
geom_in = LineString([[500000, 80000], [500000, 90000]])
geom_intersects = LineString([[500000, 50000], [500000, 90000]])
geom_out = LineString([[500000, 50000], [500000, 60000]])


@pytest.fixture(scope='class')
def test_data2(dbsession):
    from c2cgeoportal_commons.models.main import (
        LayerWMS,
        OGCServer,
        OGCSERVER_TYPE_QGISSERVER,
        OGCSERVER_AUTH_STANDARD,
        RestrictionArea,
        Role,
    )
    from c2cgeoportal_commons.models.static import User

    ogc_server = OGCServer(
        name='qgisserver',
        type_=OGCSERVER_TYPE_QGISSERVER,
        image_type='image/png',
        auth=OGCSERVER_AUTH_STANDARD
    )
    dbsession.add(ogc_server)

    role1 = Role('role_no_access')
    role2 = Role('role_full_access')
    role3 = Role('role_area_access')
    roles = {role.name: role for role in (role1, role2, role3)}
    dbsession.add_all(roles.values())

    user_no_access = User('user_no_access', roles=[role1])
    user_full_access = User('user_full_access', roles=[role2])
    user_area_access = User('user_area_access', roles=[role3])
    users = {user.username: user for user in (user_no_access, user_full_access, user_area_access)}
    dbsession.add_all(users.values())

    project = QgsProject.instance()

    for node in [
        {'name': 'root', 'type': 'group', 'children': [
            {'name': 'private_group', 'type': 'group', 'children': [
                {'name': 'private_layer', 'type': 'layer'},
            ]},
        ]},
    ]:
        add_node_in_qgis_project(project, project.layerTreeRoot(), node)

    private_layer = LayerWMS(name='private_layer', layer='private_layer', public=False)
    private_layer.ogc_server = ogc_server

    dbsession.add(private_layer)


    ra1 = RestrictionArea(
        'restriction_area_no',
        layers=[private_layer],
        roles=[role1]
    )
    ra2 = RestrictionArea(
        'restriction_area_full',
        layers=[private_layer],
        roles=[role2],
        readwrite=True
    )
    ra3 = RestrictionArea(
        'restriction_area_area',
        layers=[private_layer],
        roles=[role3],
        readwrite=True,
        area=from_shape(area1, srid=21781)
    )
    restriction_areas = {ra.name: ra for ra in (ra1, ra2, ra3)}
    dbsession.add_all(restriction_areas.values())

    t = dbsession.begin_nested()

    dbsession.flush()

    yield {
        'users': users,
        'roles': roles
    }

    t.rollback()


@pytest.mark.usefixtures(
    "server_iface",
    "qgs_access_control_filter",
    "test_data2",
)
class TestAccessControlAllowToEdit():
    def test_allowToEdit(self, server_iface, dbsession, test_data2):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver',
            21781,
            dbsession
        )

        for user_name, expected, geometry in [
            ['user_no_access', False, geom_in],
            ['user_full_access', True, geom_in],
            ['user_area_access', True, geom_in],
            ['user_no_access', False, geom_intersects],
            ['user_full_access', True, geom_intersects],
            ['user_area_access', True, geom_intersects],
            ['user_no_access', False, geom_out],
            ['user_full_access', True, geom_out],
            ['user_area_access', False, geom_out],
        ]:
            user = test_data2['users'][user_name]
            set_request_parameters(server_iface, {
                'USER_ID': str(user.id)
            })
            layer = QgsProject.instance().mapLayersByName('private_layer')[0]
            feature = QgsFeature()
            geom = QgsGeometry()
            geom.fromWkb(geometry.wkb)
            feature.setGeometry(geom)
            result = ogcserver_accesscontrol.allowToEdit(layer, feature)
            assert expected == result, (
                "allowToEdit with '{}', should return '{}'.".format(user_name, expected)
            )
