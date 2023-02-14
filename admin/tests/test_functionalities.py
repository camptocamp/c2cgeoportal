# pylint: disable=no-self-use

import re

import pytest

from . import AbstractViewsTests


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def functionality_test_data(dbsession, transact, settings):
    del transact

    from c2cgeoportal_commons.models.main import Functionality

    functionalities = []
    for i in range(0, 4):
        functionality = Functionality(
            settings["admin_interface"]["available_functionalities"][i]["name"],
            value=f"value_{i}",
        )
        functionality.description = f"description_{i}"
        dbsession.add(functionality)
        functionalities.append(functionality)

    dbsession.flush()

    yield {"functionalities": functionalities}


@pytest.mark.usefixtures("functionality_test_data", "test_app")
class TestFunctionality(AbstractViewsTests):
    _prefix = "/admin/functionalities"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "Functionalities")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name", "true"),
            ("description", "Description", "true"),
            ("value", "Value", "true"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_search(self, test_app):
        # search on functionality name
        self.check_search(test_app, "default_basemap", total=1)

    def test_submit_new(self, dbsession, test_app):
        from c2cgeoportal_commons.models.main import Functionality, Log, LogAction

        resp = test_app.post(
            "/admin/functionalities/new",
            {"name": "new_name", "description": "new_description", "value": "new_value"},
            status=302,
        )
        functionality = dbsession.query(Functionality).filter(Functionality.name == "new_name").one()
        assert str(functionality.id) == re.match(
            r"http://localhost/admin/functionalities/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
        assert functionality.name == "new_name"

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.INSERT
        assert log.element_type == "functionality"
        assert log.element_id == functionality.id
        assert log.element_name == functionality.name
        assert log.username == "test_user"

    def test_edit(self, test_app, functionality_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Log, LogAction

        functionality = functionality_test_data["functionalities"][0]
        resp = test_app.get(f"/admin/functionalities/{functionality.id}", status=200)
        form = resp.form
        assert str(functionality.id) == self.get_first_field_named(form, "id").value
        assert "hidden" == self.get_first_field_named(form, "id").attrs["type"]
        assert functionality.name == form["name"].value
        form["description"] = "new_description"
        assert form.submit().status_int == 302
        assert functionality.description == "new_description"

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.UPDATE
        assert log.element_type == "functionality"
        assert log.element_id == functionality.id
        assert log.element_name == functionality.name
        assert log.username == "test_user"

    def test_delete(self, test_app, functionality_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Functionality, Log, LogAction

        functionality = functionality_test_data["functionalities"][0]
        deleted_id = functionality.id
        test_app.delete(f"/admin/functionalities/{deleted_id}", status=200)
        assert dbsession.query(Functionality).get(deleted_id) is None

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.DELETE
        assert log.element_type == "functionality"
        assert log.element_id == functionality.id
        assert log.element_name == functionality.name
        assert log.username == "test_user"

    def test_duplicate(self, functionality_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import Functionality

        functionality = functionality_test_data["functionalities"][3]

        resp = test_app.get(f"/admin/functionalities/{functionality.id}/duplicate", status=200)

        form = resp.form
        assert form["name"].value == functionality.name
        assert form["description"].value == functionality.description
        assert form["value"].value == functionality.value
        form["value"].value = "another_value"
        resp = form.submit("submit")

        assert resp.status_int == 302
        functionality = (
            dbsession.query(Functionality)
            .filter(Functionality.name == functionality.name)
            .filter(Functionality.value == "another_value")
            .one()
        )
        assert str(functionality.id) == re.match(
            r"http://localhost/admin/functionalities/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
