# Copyright (c) 2024, Camptocamp SA
# All rights reserved.

# This program is free software; you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.

from unittest.mock import patch

import pytest
from qgis.core import QgsProject
from shapely.geometry import box

from geomapfish_qgisserver.accesscontrol import (
    GeoMapFishAccessControl,
    OGCServerAccessControl,
)

from .accesscontrol_test import add_node_in_qgis_project, set_request_parameters

area1 = box(485869.5728, 76443.1884, 837076.5648, 299941.7864)


@pytest.fixture(scope="module")
def qgis_project():
    project = QgsProject.instance()

    for node in [
        {
            "name": "root",
            "type": "group",
            "children": [
                {
                    "name": "ows_private_group1",
                    "type": "group",
                    "children": [{"name": "ows_private_layer1", "type": "layer"}],
                },
                {"name": "ows_private_layer2", "type": "layer"},
            ],
        }
    ]:
        add_node_in_qgis_project(project, project.layerTreeRoot(), node)

    yield {
        "project": project,
    }


def _test_data_protected(clean_dbsession, protected: bool):
    from c2cgeoportal_commons.models.main import (
        OGCSERVER_AUTH_STANDARD,
        OGCSERVER_TYPE_QGISSERVER,
        Functionality,
        LayerWMS,
        Metadata,
        OGCServer,
        Role,
    )
    from c2cgeoportal_commons.models.static import User

    DBSession = clean_dbsession  # noqa: ignore=N806

    dbsession = DBSession()
    for cls in [
        LayerWMS,
        OGCServer,
        Role,
        User,
        Functionality,
        Metadata,
    ]:
        for obj in dbsession.query(cls).all():
            dbsession.delete(obj)

    ogc_server = OGCServer(
        name="qgisserver1",
        type_=OGCSERVER_TYPE_QGISSERVER,
        url="http://qgis",
        image_type="image/png",
        auth=OGCSERVER_AUTH_STANDARD,
    )
    dbsession.add(ogc_server)

    role1 = Role("role")
    if protected:
        role1.functionalities = [
            Functionality("allowed_attributes", "ows_private_layer1:protected1,protected2"),
            Functionality("allowed_attributes", "ows_private_layer2:protected1,protected2"),
        ]
    dbsession.add(role1)

    user = User("user", roles=[role1])
    dbsession.add(user)

    private_layer = LayerWMS(name="private_layer", layer="ows_private_layer2", public=False)
    private_layer.ogc_server = ogc_server
    if protected:
        metadata = Metadata("protectedAttributes", "protected1,protected2,protected3")
        metadata.item = private_layer
        dbsession.add(metadata)
        dbsession.flush()
        private_layer.metadatas = [metadata]

    private_group = LayerWMS(name="private_group", layer="ows_private_group1", public=False)
    private_group.ogc_server = ogc_server
    if protected:
        metadata = Metadata("protectedAttributes", "protected1,protected2,protected3")
        metadata.item = private_group
        dbsession.add(metadata)
        dbsession.flush()
        private_group.metadatas = [metadata]

    dbsession.add_all((private_layer, private_group))

    dbsession.flush()

    role_id = role1.id
    user_id = user.id

    dbsession.commit()
    dbsession.close()

    return {
        "role": role_id,
        "user": user_id,
    }


@pytest.fixture(scope="module")
def test_data_not_protected(clean_dbsession):
    from c2cgeoportal_commons.models.main import (
        Functionality,
        LayerWMS,
        Metadata,
        OGCServer,
        Role,
    )
    from c2cgeoportal_commons.models.static import User

    test_data = _test_data_protected(clean_dbsession, False)
    yield test_data

    DBSession = clean_dbsession  # noqa: ignore=N806
    dbsession = DBSession()
    for cls in [LayerWMS, OGCServer, Role, User, Functionality, Metadata]:
        for obj in dbsession.query(cls).all():
            dbsession.delete(obj)
    dbsession.commit()


@pytest.fixture(scope="module")
def test_data_protected(clean_dbsession):
    from c2cgeoportal_commons.models.main import (
        Functionality,
        LayerWMS,
        Metadata,
        OGCServer,
        Role,
    )
    from c2cgeoportal_commons.models.static import User

    test_data = _test_data_protected(clean_dbsession, True)
    yield test_data

    DBSession = clean_dbsession  # noqa: ignore=N806
    dbsession = DBSession()
    for cls in [LayerWMS, OGCServer, Role, User, Functionality, Metadata]:
        for obj in dbsession.query(cls).all():
            dbsession.delete(obj)
    dbsession.commit()


@pytest.mark.usefixtures(
    "qgs_access_control_filter",
    "auto_single_ogc_server_env",
    "test_data_not_protected",
    "qgis_project",
)
class TestNotProtectedAttributes:
    def test_restricted_attribute(self, server_iface, test_data_not_protected, qgis_project):
        with patch(
            "geomapfish_qgisserver.accesscontrol.OGCServerAccessControl.project",
            return_value=qgis_project["project"],
        ):
            plugin = GeoMapFishAccessControl(server_iface)
            assert plugin.single is True
            assert isinstance(plugin.ogcserver_accesscontrol, OGCServerAccessControl)
            assert plugin.ogcserver_accesscontrol.ogcserver.name == "qgisserver1"

            qgis_layer = qgis_project["project"].mapLayersByName("ows_private_layer2")[0]
            qgis_layer_in_group = qgis_project["project"].mapLayersByName("ows_private_layer1")[0]

            set_request_parameters(server_iface, {"USER_ID": "0"})

            assert plugin.authorizedLayerAttributes(
                qgis_layer,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2", "protected3"]
            assert plugin.authorizedLayerAttributes(
                qgis_layer_in_group,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2", "protected3"]

            set_request_parameters(server_iface, {"ROLE_IDS": str(test_data_not_protected["role"])})

            assert plugin.authorizedLayerAttributes(
                qgis_layer,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2", "protected3"]
            assert plugin.authorizedLayerAttributes(
                qgis_layer_in_group,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2", "protected3"]

            set_request_parameters(server_iface, {})

            assert plugin.authorizedLayerAttributes(
                qgis_layer,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2", "protected3"]
            assert plugin.authorizedLayerAttributes(
                qgis_layer_in_group,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2", "protected3"]


@pytest.mark.usefixtures(
    "qgs_access_control_filter",
    "auto_single_ogc_server_env",
    "test_data_protected",
    "qgis_project",
)
class TestProtectedAttributes:
    def test_restricted_attribute(self, server_iface, test_data_protected, qgis_project):
        with patch(
            "geomapfish_qgisserver.accesscontrol.OGCServerAccessControl.project",
            return_value=qgis_project["project"],
        ):
            plugin = GeoMapFishAccessControl(server_iface)
            assert plugin.single is True
            assert isinstance(plugin.ogcserver_accesscontrol, OGCServerAccessControl)
            assert plugin.ogcserver_accesscontrol.ogcserver.name == "qgisserver1"

            qgis_layer = qgis_project["project"].mapLayersByName("ows_private_layer2")[0]
            qgis_layer_in_group = qgis_project["project"].mapLayersByName("ows_private_layer1")[0]

            set_request_parameters(server_iface, {"USER_ID": "0"})

            assert plugin.authorizedLayerAttributes(
                qgis_layer,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2", "protected3"]
            assert plugin.authorizedLayerAttributes(
                qgis_layer_in_group,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2", "protected3"]

            set_request_parameters(server_iface, {"ROLE_IDS": str(test_data_protected["role"])})

            assert plugin.authorizedLayerAttributes(
                qgis_layer,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2"]
            assert plugin.authorizedLayerAttributes(
                qgis_layer_in_group,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public", "protected1", "protected2"]

            set_request_parameters(server_iface, {})

            assert plugin.authorizedLayerAttributes(
                qgis_layer,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public"]
            assert plugin.authorizedLayerAttributes(
                qgis_layer_in_group,
                ["public", "protected1", "protected2", "protected3"],
            ) == ["public"]
