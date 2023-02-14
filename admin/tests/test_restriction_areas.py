# pylint: disable=no-self-use


import json
import re

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon, box, shape

from .test_treegroup import TestTreeGroup


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def restriction_area_test_data(dbsession, transact):
    del transact
    from c2cgeoportal_commons.models.main import LayerWMS, OGCServer, RestrictionArea, Role

    roles = []
    for i in range(0, 4):
        roles.append(Role("secretary_" + str(i)))
    dbsession.add_all(roles)

    ogc_server = OGCServer(name="test_server")
    layers = []
    for i in range(0, 4):
        layer = LayerWMS(name=f"layer_{i}", layer=f"layer_{i}", public=False)
        layer.ogc_server = ogc_server
        layers.append(layer)
    dbsession.add_all(layers)

    restrictionareas = []
    for i in range(0, 4):
        restrictionarea = RestrictionArea(name=f"restrictionarea_{i}")
        restrictionarea.area = from_shape(box(485869.5728, 76443.1884, 837076.5648, 299941.7864), srid=21781)
        restrictionarea.description = f"description_{i}"
        restrictionarea.roles = [roles[i % 4], roles[(i + 2) % 4]]
        restrictionarea.layers = [layers[i % 4], layers[(i + 2) % 4]]
        dbsession.add(restrictionarea)
        restrictionareas.append(restrictionarea)

    dbsession.flush()
    yield {
        "layers": layers,
        "restriction_areas": restrictionareas,
        "roles": roles,
    }


@pytest.mark.usefixtures("restriction_area_test_data", "test_app")
class TestRestrictionAreaViews(TestTreeGroup):
    _prefix = "/admin/restriction_areas"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "Restriction areas")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name", "true"),
            ("description", "Description", "true"),
            ("readwrite", "Read/write", "true"),
            ("roles", "Roles", "false"),
            ("layers", "Layers", "false"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_search(self, test_app):
        self.check_search(test_app, "restrictionarea_1", total=1)

    def test_submit_new(self, dbsession, test_app, restriction_area_test_data):
        from c2cgeoportal_commons.models.main import Log, LogAction, RestrictionArea

        roles = restriction_area_test_data["roles"]
        layers = restriction_area_test_data["layers"]

        resp = test_app.post(
            "/admin/restriction_areas/new",
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("id", ""),
                ("name", "new_name"),
                ("description", "new_description"),
                ("readwrite", "true"),
                ("area", ""),
                ("__start__", "roles:sequence"),
                ("roles", str(roles[0].id)),
                ("roles", str(roles[1].id)),
                ("__end__", "roles:sequence"),
                ("__start__", "layers:sequence"),
                ("__start__", "layer:mapping"),
                ("id", str(layers[0].id)),
                ("__end__", "layer:mapping"),
                ("__start__", "layer:mapping"),
                ("id", str(layers[1].id)),
                ("__end__", "layer:mapping"),
                ("__end__", "layers:sequence"),
                ("formsubmit", "formsubmit"),
            ),
            status=302,
        )

        restriction_area = dbsession.query(RestrictionArea).filter(RestrictionArea.name == "new_name").one()
        assert str(restriction_area.id) == re.match(
            r"http://localhost/admin/restriction_areas/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

        assert restriction_area.name == "new_name"
        assert restriction_area.description == "new_description"
        assert restriction_area.readwrite
        assert set(restriction_area.roles) == {roles[0], roles[1]}
        assert set(restriction_area.layers) == {layers[0], layers[1]}

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.INSERT
        assert log.element_type == "restrictionarea"
        assert log.element_id == restriction_area.id
        assert log.element_name == restriction_area.name
        assert log.username == "test_user"

    def test_unicity_validator(self, restriction_area_test_data, test_app):
        restriction_area = restriction_area_test_data["restriction_areas"][2]

        resp = test_app.get(f"/admin/restriction_areas/{restriction_area.id}/duplicate", status=200)
        resp = resp.form.submit("submit")

        self._check_submission_problem(resp, f"{restriction_area.name} is already used.")

    def test_edit(self, test_app, restriction_area_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Log, LogAction

        restriction_area = restriction_area_test_data["restriction_areas"][0]
        roles = restriction_area_test_data["roles"]

        # Ensure restriction_area.layers is loaded with relationship "order_by"
        dbsession.expire(restriction_area)

        form = self.get_item(test_app, restriction_area.id).form

        assert str(restriction_area.id) == self.get_first_field_named(form, "id").value
        assert "hidden" == self.get_first_field_named(form, "id").attrs["type"]
        assert restriction_area.name == form["name"].value
        expected = Polygon(
            [
                (1167544.3397631699, 5748064.729594703),
                (1180453.0256760044, 6074797.96820131),
                (658348.6696383564, 6080273.63626964),
                (664577.4194513536, 5753148.2510447875),
                (1167544.3397631699, 5748064.729594703),
            ]
        )
        assert expected.almost_equals(shape(json.loads(form["area"].value)), decimal=0)
        self._check_roles(form, roles, restriction_area)
        self.check_children(
            form,
            "layers",
            [
                {"label": layer.name, "values": {"id": str(layer.id)}}
                for layer in sorted(restriction_area.layers, key=lambda l: l.name)
            ],
        )

        form["description"] = "new_description"
        form["roles"] = [roles[i].id for i in range(0, 3)]
        form.submit("submit")

        dbsession.expire(restriction_area)
        assert restriction_area.description == "new_description"
        assert set(restriction_area.roles) == {roles[i] for i in range(0, 3)}

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.UPDATE
        assert log.element_type == "restrictionarea"
        assert log.element_id == restriction_area.id
        assert log.element_name == restriction_area.name
        assert log.username == "test_user"

    def test_delete(self, test_app, restriction_area_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Log, LogAction, RestrictionArea

        restriction_area = restriction_area_test_data["restriction_areas"][0]
        deleted_id = restriction_area.id
        test_app.delete(f"/admin/restriction_areas/{deleted_id}", status=200)
        assert dbsession.query(RestrictionArea).get(deleted_id) is None

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.DELETE
        assert log.element_type == "restrictionarea"
        assert log.element_id == restriction_area.id
        assert log.element_name == restriction_area.name
        assert log.username == "test_user"

    def test_duplicate(self, restriction_area_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import RestrictionArea

        restriction_area = restriction_area_test_data["restriction_areas"][3]
        roles = restriction_area_test_data["roles"]

        # Ensure restriction_area.layers is loaded with relationship "order_by"
        dbsession.expire(restriction_area)

        form = test_app.get(f"/admin/restriction_areas/{restriction_area.id}/duplicate", status=200).form

        assert "" == self.get_first_field_named(form, "id").value
        self._check_roles(form, roles, restriction_area)
        self.check_children(
            form,
            "layers",
            [
                {"label": layer.name, "values": {"id": str(layer.id)}}
                for layer in sorted(restriction_area.layers, key=lambda l: l.name)
            ],
        )

        self.set_first_field_named(form, "name", "clone")
        resp = form.submit("submit")

        assert resp.status_int == 302
        restriction_area = dbsession.query(RestrictionArea).filter(RestrictionArea.name == "clone").one()
        assert str(restriction_area.id) == re.match(
            r"http://localhost/admin/restriction_areas/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
