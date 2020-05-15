# -*- coding: utf-8 -*-

# Copyright (c) 2018-2020, Camptocamp SA
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

from geoalchemy2.shape import from_shape
import pytest
from qgis.core import QgsFeature, QgsGeometry, QgsProject
from shapely.geometry import LineString, box

from geomapfish_qgisserver.accesscontrol import OGCServerAccessControl

from .accesscontrol_test import add_node_in_qgis_project, set_request_parameters

area1 = box(400000, 70000, 800000, 100000)
geom_in = LineString([[500000, 80000], [500000, 90000]])
geom_intersects = LineString([[500000, 50000], [500000, 90000]])
geom_out = LineString([[500000, 50000], [500000, 60000]])


@pytest.fixture(scope="class")
def test_data2(DBSession):  # noqa: N803
    from c2cgeoportal_commons.models.main import (
        LayerWMS,
        OGCServer,
        OGCSERVER_TYPE_QGISSERVER,
        OGCSERVER_AUTH_STANDARD,
        RestrictionArea,
        Role,
        role_ra,
        layer_ra,
        TreeItem,
    )
    from c2cgeoportal_commons.models.static import User, user_role

    dbsession = DBSession()
    dbsession.execute(layer_ra.delete())
    dbsession.query(TreeItem).delete()
    dbsession.query(OGCServer).delete()
    dbsession.execute(role_ra.delete())
    dbsession.query(RestrictionArea).delete()
    dbsession.execute(user_role.delete())
    dbsession.query(User).delete()
    dbsession.query(Role).delete()
    dbsession.commit()
    DBSession.remove()

    dbsession = DBSession()

    for r in dbsession.query(TreeItem).all():
        print(r.id)

    ogc_server1 = OGCServer(
        name="qgisserver",
        type_=OGCSERVER_TYPE_QGISSERVER,
        image_type="image/png",
        auth=OGCSERVER_AUTH_STANDARD,
    )
    dbsession.add(ogc_server1)

    role1 = Role("role_no_access")
    role2 = Role("role_full_access")
    role3 = Role("role_area_access")
    dbsession.add_all((role1, role2, role3))

    user_no_access = User("user_no_access", roles=[role1])
    user_full_access = User("user_full_access", roles=[role2])
    user_area_access = User("user_area_access", roles=[role3])
    dbsession.add_all((user_no_access, user_full_access, user_area_access))

    project = QgsProject.instance()

    for node in [
        {
            "name": "root",
            "type": "group",
            "children": [
                {
                    "name": "private_group",
                    "type": "group",
                    "children": [{"name": "private_layer", "type": "layer"}],
                },
            ],
        },
    ]:
        add_node_in_qgis_project(project, project.layerTreeRoot(), node)

    private_layer = LayerWMS(name="private_layer", layer="private_layer", public=False)
    private_layer.ogc_server = ogc_server1

    dbsession.add(private_layer)

    ra1 = RestrictionArea("restriction_area_no", layers=[private_layer], roles=[role1])
    ra2 = RestrictionArea("restriction_area_full", layers=[private_layer], roles=[role2], readwrite=True)
    ra3 = RestrictionArea(
        "restriction_area_area",
        layers=[private_layer],
        roles=[role3],
        readwrite=True,
        area=from_shape(area1, srid=21781),
    )
    dbsession.add_all((ra1, ra2, ra3))

    dbsession.flush()

    roles = {role.name: {"id": role.id} for role in (role1, role2, role3)}
    users = {
        user.username: {"id": user.id, "role_ids": [r.id for r in user.roles]}
        for user in (user_no_access, user_full_access, user_area_access)
    }

    dbsession.commit()
    DBSession.remove()

    yield {
        "users": users,
        "roles": roles,
        "project": project,
    }

    dbsession = DBSession()
    dbsession.execute(layer_ra.delete())
    dbsession.query(TreeItem).delete()
    dbsession.query(OGCServer).delete()
    dbsession.execute(role_ra.delete())
    dbsession.query(RestrictionArea).delete()
    dbsession.execute(user_role.delete())
    dbsession.query(User).delete()
    dbsession.query(Role).delete()
    dbsession.commit()
    DBSession.remove()


@pytest.mark.usefixtures(
    "server_iface", "qgs_access_control_filter", "test_data2",
)
class TestAccessControlAllowToEdit:
    def test_allow_to_edit(self, server_iface, DBSession, test_data2):  # noqa: N803
        session = DBSession()
        ogcserver_accesscontrol = OGCServerAccessControl(
            server_iface, "qgisserver", "no_project", 21781, lambda: session
        )
        ogcserver_accesscontrol.project = test_data2["project"]

        for user_name, expected, geometry in [
            ["user_no_access", False, geom_in],
            ["user_full_access", True, geom_in],
            ["user_area_access", True, geom_in],
            ["user_no_access", False, geom_intersects],
            ["user_full_access", True, geom_intersects],
            ["user_area_access", True, geom_intersects],
            ["user_no_access", False, geom_out],
            ["user_full_access", True, geom_out],
            ["user_area_access", False, geom_out],
        ]:
            user = test_data2["users"][user_name]
            set_request_parameters(
                server_iface,
                {"USER_ID": str(user["id"]), "ROLE_IDS": ",".join([str(e) for e in user["role_ids"]])},
            )

            layer = test_data2["project"].mapLayersByName("private_layer")[0]
            feature = QgsFeature()
            geom = QgsGeometry()
            geom.fromWkb(geometry.wkb)
            feature.setGeometry(geom)
            result = ogcserver_accesscontrol.allowToEdit(layer, feature)
            assert expected == result, "allowToEdit with '{}', should return '{}'.".format(
                user_name, expected
            )
