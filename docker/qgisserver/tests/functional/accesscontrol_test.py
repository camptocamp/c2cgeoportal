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
import pytest
from unittest.mock import Mock, patch

from qgis.core import QgsProject, QgsVectorLayer
from qgis.server import QgsServerInterface

from geoalchemy2.shape import from_shape
from shapely.geometry import box

from geomapfish_qgisserver.accesscontrol import (
    Access,
    GeoMapFishAccessControl,
    OGCServerAccessControl,
)

area1 = box(485869.5728, 76443.1884, 837076.5648, 299941.7864)


@pytest.fixture(scope='module')
def scoped_session(dbsession):
    with patch('geomapfish_qgisserver.accesscontrol.scoped_session',
               return_value=dbsession) as mock:
        yield mock


@pytest.fixture(scope='function')
def server_iface():
    yield Mock(spec=QgsServerInterface)


def set_request_parameters(server_iface, params):
    server_iface.configure_mock(**{
        'requestHandler.return_value': Mock(**{
            'parameterMap.return_value': params,
            'parameter.side_effect': lambda key: params[key]})})


@pytest.fixture(scope='module')
def qgs_access_control_filter():
    """
    Mock some QgsAccessControlFilter methods:
    - __init__ which does not accept a mocked QgsServerInterface;
    - serverInterface to return the right server_iface.
    """
    class DummyQgsAccessControlFilter():

        def __init__(self, server_iface):
            self.server_iface = server_iface

        def serverInterface(self):  # noqa
            return self.server_iface

    with patch.multiple('geomapfish_qgisserver.accesscontrol.QgsAccessControlFilter',
                        __init__=DummyQgsAccessControlFilter.__init__,
                        serverInterface=DummyQgsAccessControlFilter.serverInterface) as mocks:
        yield mocks


@pytest.fixture(scope='class')
def single_ogc_server_env(dbsession):
    os.environ['GEOMAPFISH_OGCSERVER'] = 'qgisserver1'
    yield
    del os.environ['GEOMAPFISH_OGCSERVER']


@pytest.fixture(scope='class')
def multiple_ogc_server_env(dbsession):
    os.environ['GEOMAPFISH_ACCESSCONTROL_CONFIG'] = '/etc/qgisserver/multiple_ogc_server.yaml'
    yield
    del os.environ['GEOMAPFISH_ACCESSCONTROL_CONFIG']


@pytest.fixture(scope='module')
def test_data(dbsession):
    from c2cgeoportal_commons.models.main import (
        LayerWMS,
        OGCServer,
        OGCSERVER_TYPE_QGISSERVER,
        OGCSERVER_AUTH_STANDARD,
        RestrictionArea,
        Role,
    )
    from c2cgeoportal_commons.models.static import User

    ogc_server1 = OGCServer(
        name='qgisserver1',
        type_=OGCSERVER_TYPE_QGISSERVER,
        image_type='image/png',
        auth=OGCSERVER_AUTH_STANDARD
    )
    ogc_server2 = OGCServer(
        name='qgisserver2',
        type_=OGCSERVER_TYPE_QGISSERVER,
        image_type='image/png',
        auth=OGCSERVER_AUTH_STANDARD
    )
    ogc_servers = {ogc_server.name: ogc_server for ogc_server in (ogc_server1, ogc_server2)}
    dbsession.add_all(ogc_servers.values())

    role1 = Role('role1')
    role2 = Role('role2')
    roles = {role.name: role for role in (role1, role2)}
    dbsession.add_all(roles.values())

    root = User('root')
    root.id = 0
    user1 = User('user1', roles=[role1])
    user2 = User('user12', roles=[role1, role2])
    users = {user.username: user for user in (root, user1, user2)}
    dbsession.add_all(users.values())

    project = QgsProject.instance()

    def add_node(parent_node, node_def):

        if node_def['type'] == 'layer':
            vlayer = QgsVectorLayer("Point", node_def['name'], 'memory')
            if 'shortName' in node_def:
                vlayer.setShortName(node_def['shortName'])
            project.addMapLayer(vlayer)
            node = project.layerTreeRoot().findLayer(vlayer)
            clone = node.clone()
            parent_node.addChildNode(clone)
            node.parent().takeChild(node)

        if node_def['type'] == 'group':
            node = parent_node.addGroup(node_def['name'])
            if 'shortName' in node_def:
                node.setCustomProperty("wmsShortName", node_def['shortName'])
            for child_def in node_def['children']:
                add_node(node, child_def)

    for node in [
        {'name': 'root', 'type': 'group', 'children': [
            {'name': 'public_group', 'type': 'group', 'children': [
                {'name': 'public_layer', 'type': 'layer'},
            ]},
            {'name': 'private_group1', 'type': 'group', 'children': [
                {'name': 'private_layer1', 'type': 'layer'},
            ]},
            {'name': 'private_group2', 'type': 'group', 'children': [
                {'name': 'private_layer2', 'type': 'layer'},
            ]},
            # For group and layer short names
            {'name': 'private_group3', 'type': 'group', 'shortName': 'pg3', 'children': [
                {'name': 'private_layer3', 'type': 'layer', 'shortName': 'pl3'},
            ]},
        ]},
    ]:
        add_node(project.layerTreeRoot(), node)

    public_group = LayerWMS(name='public_group', layer='public_group', public=True)
    public_group.ogc_server = ogc_server1

    public_layer = LayerWMS(name='public_layer', layer='public_layer', public=True)
    public_layer.ogc_server = ogc_server1

    private_layer1 = LayerWMS(name='private_layer1', layer='private_layer1', public=False)
    private_layer1.ogc_server = ogc_server1

    private_layer2 = LayerWMS(name='private_layer2', layer='private_layer2', public=False)
    private_layer2.ogc_server = ogc_server1

    private_group3 = LayerWMS(name='private_group3', layer='pg3', public=False)
    private_group3.ogc_server = ogc_server1

    private_layer3 = LayerWMS(name='private_layer3', layer='pl3', public=False)
    private_layer3.ogc_server = ogc_server1

    layers = {layer.name: layer for layer in (
        public_group, public_layer, private_layer1, private_layer2, private_group3, private_layer3
    )}
    dbsession.add_all(layers.values())

    ra1 = RestrictionArea('restriction_area1',
                          layers=[private_layer1, private_layer3],
                          roles=[role1],
                          area=from_shape(area1, srid=21781))
    ra2 = RestrictionArea('restriction_area2',
                          layers=[private_layer2],
                          roles=[role2],
                          readwrite=True)
    restriction_areas = {ra.name: ra for ra in (ra1, ra2)}
    dbsession.add_all(restriction_areas.values())

    t = dbsession.begin_nested()

    dbsession.flush()

    yield {
        'ogc_servers': ogc_servers,
        'roles': roles,
        'users': users,
        'layers': layers,
        'restriction_areas': restriction_areas,
    }

    t.rollback()


@pytest.fixture(scope='function')
def wms_use_layer_ids():
    """
    Activate WMSUseLayerIDs
    """
    project = QgsProject.instance()
    try:
        project.writeEntry("WMSUseLayerIDs", "/", True)
        yield
    finally:
        project.writeEntry("WMSUseLayerIDs", "/", False)


@pytest.mark.usefixtures("server_iface",
                         "qgs_access_control_filter",
                         "test_data")
class TestOGCServerAccessControl():

    def test_init(self, server_iface, dbsession, test_data):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )
        assert ogcserver_accesscontrol.ogcserver is test_data['ogc_servers']['qgisserver1']

    def test_ogc_layer_name(self, server_iface, dbsession):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )
        for layer_name, expected in (
            ('private_layer1', 'private_layer1'),
            ('private_layer3', 'pl3'),
        ):
            layer = QgsProject.instance().mapLayersByName(layer_name)[0]
            assert expected == ogcserver_accesscontrol.ogc_layer_name(layer)

    @pytest.mark.usefixtures("wms_use_layer_ids")
    def test_ogc_layer_with_wms_use_layer_ids(self, server_iface, dbsession):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )
        layer = QgsProject.instance().mapLayersByName('private_layer1')[0]
        assert layer.id() == ogcserver_accesscontrol.ogc_layer_name(layer)

    def test_get_layers(self, server_iface, dbsession, test_data):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )

        test_layers = test_data['layers']
        expected = {
            'public_group': [test_layers['public_group']],
            'public_layer': [test_layers['public_group'],
                             test_layers['public_layer']],
            'private_layer1': [test_layers['private_layer1']],
            'private_layer2': [test_layers['private_layer2']],
            'pg3': [test_layers['private_group3']],
            'pl3': [test_layers['private_group3'],
                    test_layers['private_layer3']],
        }

        layers = ogcserver_accesscontrol.get_layers()

        assert set(expected.keys()) == set(layers.keys())
        for key in expected.keys():
            assert set(expected[key]) == set(layers[key])

    def test_get_roles(self, server_iface, dbsession, test_data):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )

        set_request_parameters(server_iface, {'USER_ID': '0'})
        assert 'ROOT' == ogcserver_accesscontrol.get_roles()

        test_users = test_data['users']
        test_roles = test_data['roles']

        for user_name, expected_role_names in (
            ('user1', ('role1',)),
            ('user12', ('role1', 'role2')),
        ):
            set_request_parameters(server_iface, {
                'USER_ID': str(test_users[user_name].id)
            })
            expected_roles = {test_roles[expected_role_name]
                              for expected_role_name in expected_role_names}
            assert expected_roles == set(ogcserver_accesscontrol.get_roles())

    def test_get_restriction_areas(self, server_iface, dbsession, test_data):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )

        test_layers = test_data['layers']
        test_roles = test_data['roles']

        assert (Access.FULL, None) == ogcserver_accesscontrol.get_restriction_areas(
            (test_layers['private_layer1'],),
            rw=True,
            roles='ROOT')

        for layer_names, rw, role_names, expected in (
            (('private_layer1',), False, ('role1',), (Access.AREA, [area1])),
            (('private_layer3',), False, ('role1',), (Access.AREA, [area1])),
        ):
            layers = [test_layers[layer_name] for layer_name in layer_names]
            roles = [test_roles[role_name] for role_name in role_names]
            ras = ogcserver_accesscontrol.get_restriction_areas(layers, rw, roles)
            assert expected == ras, (
                'get_restriction_areas with {} should return {}'.
                format((layer_names, rw, role_names), expected))

    def test_get_area(self, server_iface, dbsession, test_data):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )

        for user_name, layer_name, expected in [
            ('root', layer_name, (Access.FULL, None))
            for layer_name in (
                'public_layer',
                'private_layer1',
                'private_layer2',
                'private_layer3',
            )
        ] + [
            ('user1', 'public_layer', (Access.FULL, None)),
            ('user1', 'private_layer1', (Access.AREA, area1.wkt)),
            ('user1', 'private_layer2', (Access.NO, None)),
            ('user1', 'private_layer3', (Access.AREA, area1.wkt)),
        ]:
            user = test_data['users'][user_name]
            set_request_parameters(server_iface, {
                'USER_ID': str(user.id)
            })
            layer = QgsProject.instance().mapLayersByName(layer_name)[0]
            result = ogcserver_accesscontrol.get_area(layer)
            assert expected == result, (
                'get_area with "{}", "{}" should return {}'.
                format(user_name, layer_name, expected))

    @staticmethod
    def test_layer_permissions(server_iface, dbsession, test_data):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )

        for user_name, layer_name, expected in (
            ('user1', 'public_layer', {'canDelete': False,
                                       'canInsert': False,
                                       'canRead': True,
                                       'canUpdate': False}),
            ('user1', 'private_layer1', {'canDelete': False,
                                         'canInsert': False,
                                         'canRead': True,
                                         'canUpdate': False}),
            ('user12', 'private_layer2', {'canDelete': True,
                                          'canInsert': True,
                                          'canRead': True,
                                          'canUpdate': True}),
        ):
            user = test_data['users'][user_name]
            set_request_parameters(server_iface, {
                'USER_ID': str(user.id)
            })
            layer = QgsProject.instance().mapLayersByName(layer_name)[0]
            permissions = ogcserver_accesscontrol.layerPermissions(layer)
            for key, value in expected.items():
                assert value == getattr(permissions, key)

    @staticmethod
    def test_cache_key(server_iface, dbsession, test_data):
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface,
            'qgisserver1',
            21781,
            dbsession
        )

        set_request_parameters(server_iface, {
            'Host': 'example.com',
            'USER_ID': '0'
        })
        assert '0' == server_iface.requestHandler().parameter("USER_ID")
        assert 'example.com' == server_iface.requestHandler().parameter("Host")
        assert 'example.com--1' == ogcserver_accesscontrol.cacheKey()

        user = test_data['users']['user12']
        set_request_parameters(server_iface, {
            'Host': 'example.com',
            'USER_ID': str(user.id)
        })
        role1 = test_data['roles']['role1']
        role2 = test_data['roles']['role2']
        expected = 'example.com-{}'.format(','.join([str(role1.id), str(role2.id)]))
        assert expected == ogcserver_accesscontrol.cacheKey()


@pytest.mark.usefixtures("server_iface",
                         "qgs_access_control_filter",
                         "single_ogc_server_env",
                         "scoped_session",
                         "test_data")
class TestGeoMapFishAccessControlSingleOGCServer():

    def test_init(self, server_iface):
        plugin = GeoMapFishAccessControl(server_iface)
        assert plugin.single is True
        assert isinstance(plugin.ogcserver_accesscontrol, OGCServerAccessControl)


@pytest.mark.usefixtures("qgs_access_control_filter",
                         "multiple_ogc_server_env",
                         "scoped_session",
                         "test_data")
class TestGeoMapFishAccessControlMultipleOGCServer():

    @pytest.mark.usefixtures()
    def test_init(self, server_iface, test_data):
        plugin = GeoMapFishAccessControl(server_iface)
        assert plugin.single is False

        assert plugin.serverInterface() is server_iface

        set_request_parameters(server_iface, {'MAP': 'qgsproject1'})
        assert plugin.serverInterface().requestHandler().parameterMap()['MAP'] == 'qgsproject1'
        assert plugin.get_ogcserver_accesscontrol().ogcserver is test_data['ogc_servers']['qgisserver1']

        set_request_parameters(server_iface, {'MAP': 'qgsproject2'})
        assert plugin.serverInterface().requestHandler().parameterMap()['MAP'] == 'qgsproject2'
        assert plugin.get_ogcserver_accesscontrol().ogcserver is test_data['ogc_servers']['qgisserver2']
