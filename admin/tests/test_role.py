# pylint: disable=no-self-use,unsubscriptable-object

import json
import re

import pytest
from geoalchemy2.shape import from_shape, to_shape
from pyramid.testing import DummyRequest
from shapely.geometry import Polygon, box, shape

from .test_treegroup import TestTreeGroup


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def roles_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Functionality, RestrictionArea, Role
    from c2cgeoportal_commons.models.static import User

    functionalities = {}
    for name in ("default_basemap", "location"):
        functionalities[name] = []
        for v in range(0, 4):
            functionality = Functionality(name=name, value="value_{}".format(v))
            dbsession.add(functionality)
            functionalities[name].append(functionality)

    restrictionareas = []
    for i in range(0, 5):
        restrictionarea = RestrictionArea(name="restrictionarea_{}".format(i))
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    roles = []
    for i in range(0, 23):
        role = Role("secretary_" + str(i))
        role.functionalities = [
            functionalities["default_basemap"][0],
            functionalities["location"][0],
            functionalities["location"][1],
        ]
        role.restrictionareas = [restrictionareas[0], restrictionareas[1]]
        role.extent = from_shape(box(485869.5728, 76443.1884, 837076.5648, 299941.7864), srid=21781)
        dbsession.add(role)
        roles.append(role)

    # Users roles must not be broken with role name changes
    users = []
    for i in range(0, 23):
        user = User("babar_" + str(i), email="mail" + str(i), settings_role=roles[i], roles=[roles[i]])
        user.password = "pré$ident"
        user.is_password_changed = i % 2 == 1
        users.append(user)
        dbsession.add(user)

    dbsession.flush()

    yield {
        "functionalities": functionalities,
        "restrictionareas": restrictionareas,
        "users": users,
        "roles": roles,
    }


@pytest.mark.usefixtures("roles_test_data", "test_app")
class TestRole(TestTreeGroup):

    _prefix = "/admin/roles"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "Roles")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name"),
            ("description", "Description"),
            ("functionalities", "Functionalities", "false"),
            ("restrictionareas", "Restriction areas", "false"),
        ]
        self.check_grid_headers(resp, expected)

    @pytest.mark.skip(reason="Translation seems not available in tests")
    def test_index_rendering_fr(self, test_app):
        resp = self.get(test_app, locale="fr")

        self.check_left_menu(resp, "Rôles")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Nom"),
            ("description", "Description"),
            ("functionalities", "Fonctionnalités", "false"),
            ("restrictionareas", "Zones de restriction", "false"),
        ]
        self.check_grid_headers(resp, expected, new="Nouveau")

    def test_submit_new(self, dbsession, test_app, roles_test_data):
        from c2cgeoportal_commons.models.main import Role

        roles = roles_test_data["roles"]
        functionalities = roles_test_data["functionalities"]
        restrictionareas = roles_test_data["restrictionareas"]
        users = roles_test_data["users"]

        resp = test_app.post(
            "/admin/roles/new",
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("id", ""),
                ("name", "new_name"),
                ("description", "new_description"),
                ("extent", ""),
                ("__start__", "functionalities:sequence"),
                ("functionalities", str(functionalities["default_basemap"][0].id)),
                ("functionalities", str(functionalities["location"][1].id)),
                ("__end__", "functionalities:sequence"),
                ("__start__", "restrictionareas:sequence"),
                ("restrictionareas", str(restrictionareas[0].id)),
                ("restrictionareas", str(restrictionareas[1].id)),
                ("__end__", "restrictionareas:sequence"),
                ("__start__", "users:sequence"),
                ("__start__", "user:mapping"),
                ("id", str(users[0].id)),
                ("__end__", "user:mapping"),
                ("__start__", "user:mapping"),
                ("id", str(users[1].id)),
                ("__end__", "user:mapping"),
                ("__end__", "users:sequence"),
                ("formsubmit", "formsubmit"),
            ),
            status=302,
        )

        role = dbsession.query(Role).filter(Role.name == "new_name").one()
        assert str(role.id) == re.match(
            r"http://localhost/admin/roles/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

        assert role.name == "new_name"
        assert role.description == "new_description"
        assert set(role.functionalities) == set(
            [functionalities["default_basemap"][0], functionalities["location"][1]]
        )
        assert set(role.restrictionareas) == set([restrictionareas[0], restrictionareas[1]])
        assert set(role.users) == set([users[0], users[1]])

    def test_edit(self, dbsession, test_app, roles_test_data):
        role = roles_test_data["roles"][10]

        # Ensure role.users is loaded with relationship "order_by"
        dbsession.expire(role)

        form = self.get_item(test_app, role.id).form

        assert "secretary_10" == form["name"].value

        expected = Polygon(
            [
                (1167544.3397631699, 5748064.729594703),
                (1180453.0256760044, 6074797.96820131),
                (658348.6696383564, 6080273.63626964),
                (664577.4194513536, 5753148.2510447875),
                (1167544.3397631699, 5748064.729594703),
            ]
        )
        assert expected.almost_equals(shape(json.loads(form["extent"].value)), decimal=0)

        functionalities = roles_test_data["functionalities"]
        assert (
            set(
                (
                    functionalities["default_basemap"][0].id,
                    functionalities["location"][0].id,
                    functionalities["location"][1].id,
                )
            )
            == set(f.id for f in role.functionalities)
        )
        self.check_checkboxes(
            form,
            "functionalities",
            [
                {
                    "label": "{}={}".format(f.name, f.value),
                    "value": str(f.id),
                    "checked": f in role.functionalities,
                }
                for f in sum(
                    [roles_test_data["functionalities"][name] for name in ("default_basemap", "location")], []
                )
            ],
        )

        ras = roles_test_data["restrictionareas"]
        assert set((ras[0].id, ras[1].id)) == set(ra.id for ra in role.restrictionareas)
        self.check_checkboxes(
            form,
            "restrictionareas",
            [
                {"label": ra.name, "value": str(ra.id), "checked": ra in role.restrictionareas}
                for ra in sorted(ras, key=lambda ra: ra.name)
            ],
        )

        self.check_children(
            form,
            "users",
            [
                {"label": user.username, "values": {"id": str(user.id)}}
                for user in sorted(role.users, key=lambda u: u.username)
            ],
        )

        form["name"] = "New name"
        form["description"] = "New description"
        form["extent"] = json.dumps(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1000000, 5800000],
                        [1000000, 6000000],
                        [700000, 6000000],
                        [700000, 5800000],
                        [1000000, 5800000],
                    ]
                ],
            }
        )

        functionality_ids = [
            roles_test_data["functionalities"]["default_basemap"][1].id,
            roles_test_data["functionalities"]["location"][1].id,
            roles_test_data["functionalities"]["default_basemap"][2].id,
        ]
        form["functionalities"] = [str(id) for id in functionality_ids]

        ra_ids = [roles_test_data["restrictionareas"][2].id, roles_test_data["restrictionareas"][3].id]
        form["restrictionareas"] = [str(id) for id in ra_ids]

        resp = form.submit("submit")

        assert str(role.id) == re.match(
            r"http://localhost/admin/roles/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

        dbsession.expire(role)

        assert "New name" == role.name
        assert "New description" == role.description

        expected = Polygon(
            [
                (719383.7988896352, 109062.8141734005),
                (716689.3301397888, 245909.7643546755),
                (513083.1504351135, 245400.5416369234),
                (511073.1973649057, 108541.7344432737),
                (719383.7988896352, 109062.8141734005),
            ]
        )
        assert expected.almost_equals(to_shape(role.extent), decimal=0)

        assert set(functionality_ids) == set([f.id for f in role.functionalities])
        assert set(ra_ids) == set([f.id for f in role.restrictionareas])

    def test_duplicate(self, roles_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import Role

        role_proto = roles_test_data["roles"][7]

        resp = test_app.get("/admin/roles/{}/duplicate".format(role_proto.id), status=200)
        form = resp.form

        assert "" == self.get_first_field_named(form, "id").value
        assert role_proto.name == form["name"].value
        assert role_proto.description == form["description"].value
        form["name"].value = "clone"
        resp = form.submit("submit")

        role = dbsession.query(Role).filter(Role.name == "clone").one()
        assert str(role.id) == re.match(
            r"http://localhost/admin/roles/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
        assert role_proto.id != role.id
        assert set(role_proto.functionalities) == set(role.functionalities)
        assert set(role_proto.restrictionareas) == set(role.restrictionareas)
        assert set(role_proto.users) == set(role.users)

    def test_delete(self, test_app, dbsession):
        from c2cgeoportal_commons.models.main import Role

        role_id = dbsession.query(Role.id).first().id
        test_app.delete("/admin/roles/{}".format(role_id), status=200)
        assert dbsession.query(Role).get(role_id) is None

    def test_unicity_validator(self, roles_test_data, test_app):
        role_proto = roles_test_data["roles"][7]
        resp = test_app.get("/admin/roles/{}/duplicate".format(role_proto.id), status=200)

        resp = resp.form.submit("submit")

        self._check_submission_problem(resp, "{} is already used.".format(role_proto.name))

    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.roles import RoleViews

        request = DummyRequest(dbsession=dbsession, params={"offset": 0, "limit": 10})
        info = RoleViews(request).grid()
        assert info.status_int == 500, "Expected 500 status when db error"
