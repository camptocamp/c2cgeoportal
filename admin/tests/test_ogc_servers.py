# pylint: disable=no-self-use

import re
from unittest.mock import patch

import pytest

from . import AbstractViewsTests


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def ogc_server_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import OGCServer

    auth = ["No auth", "Standard auth", "Geoserver auth", "Proxy"]
    servers = []
    for i in range(0, 8):
        server = OGCServer(name=f"server_{i}", description=f"description_{i}")
        server.url = f"https://somebasicurl_{i}.com"
        server.image_type = "image/jpeg" if i % 2 == 0 else "image/png"
        server.auth = auth[i % 4]
        dbsession.add(server)
        servers.append(server)

    dbsession.flush()

    yield {"ogc_servers": servers}


@pytest.mark.usefixtures("ogc_server_test_data", "test_app")
class TestOGCServer(AbstractViewsTests):
    _prefix = "/admin/ogc_servers"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "OGC Servers")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("name", "Name", "true"),
            ("description", "Description", "true"),
            ("url", "Basic URL", "true"),
            ("url_wfs", "WFS URL", "true"),
            ("type", "Server type", "true"),
            ("image_type", "Image type", "true"),
            ("auth", "Authentication type", "true"),
            ("wfs_support", "WFS support", "true"),
            ("is_single_tile", "Single tile", "true"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_search(self, test_app):
        # search on ogc_server name
        self.check_search(test_app, "server_0", total=1)

    def test_submit_new(self, dbsession, test_app):
        from c2cgeoportal_commons.models.main import Log, LogAction, OGCServer

        with patch("c2cgeoportal_admin.views.ogc_servers.OGCServerViews._update_cache"):
            resp = test_app.post(
                "/admin/ogc_servers/new",
                {
                    "name": "new_name",
                    "description": "new description",
                    "url": "www.randomurl.com",
                    "type": "mapserver",
                    "auth": "No auth",
                    "image_type": "image/png",
                },
                status=302,
            )
        ogc_server = dbsession.query(OGCServer).filter(OGCServer.name == "new_name").one()
        assert str(ogc_server.id) == re.match(
            r"http://localhost/admin/ogc_servers/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
        assert ogc_server.name == "new_name"

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.INSERT
        assert log.element_type == "ogc_server"
        assert log.element_id == ogc_server.id
        assert log.element_name == ogc_server.name
        assert log.username == "test_user"

    def test_edit(self, test_app, ogc_server_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Log, LogAction

        ogc_server = ogc_server_test_data["ogc_servers"][0]
        resp = test_app.get(f"/admin/ogc_servers/{ogc_server.id}", status=200)
        form = resp.form
        assert str(ogc_server.id) == self.get_first_field_named(form, "id").value
        assert "hidden" == self.get_first_field_named(form, "id").attrs["type"]
        assert ogc_server.name == form["name"].value
        form["description"] = "new_description"
        with patch("c2cgeoportal_admin.views.ogc_servers.OGCServerViews._update_cache"):
            assert form.submit().status_int == 302
        assert ogc_server.description == "new_description"

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.UPDATE
        assert log.element_type == "ogc_server"
        assert log.element_id == ogc_server.id
        assert log.element_name == ogc_server.name
        assert log.username == "test_user"

    def test_delete(self, test_app, ogc_server_test_data, dbsession):
        from c2cgeoportal_commons.models.main import Log, LogAction, OGCServer

        ogc_server = ogc_server_test_data["ogc_servers"][0]
        test_app.delete(f"/admin/ogc_servers/{ogc_server.id}", status=200)
        assert dbsession.query(OGCServer).get(ogc_server.id) is None

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.DELETE
        assert log.element_type == "ogc_server"
        assert log.element_id == ogc_server.id
        assert log.element_name == ogc_server.name
        assert log.username == "test_user"

    def test_duplicate(self, ogc_server_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import OGCServer

        ogc_server = ogc_server_test_data["ogc_servers"][3]
        resp = test_app.get(f"/admin/ogc_servers/{ogc_server.id}/duplicate", status=200)
        form = resp.form
        assert "" == self.get_first_field_named(form, "id").value
        self.set_first_field_named(form, "name", "clone")
        with patch("c2cgeoportal_admin.views.ogc_servers.OGCServerViews._update_cache"):
            resp = form.submit("submit")
        assert resp.status_int == 302
        server = dbsession.query(OGCServer).filter(OGCServer.name == "clone").one()
        assert str(server.id) == re.match(
            r"http://localhost/admin/ogc_servers/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

    def test_unicity_validator(self, ogc_server_test_data, test_app):
        ogc_server = ogc_server_test_data["ogc_servers"][3]
        resp = test_app.get(f"/admin/ogc_servers/{ogc_server.id}/duplicate", status=200)

        resp = resp.form.submit("submit")

        self._check_submission_problem(resp, f"{ogc_server.name} is already used.")

    def test_check_success(self, ogc_server_test_data, test_app):
        ogc_server = ogc_server_test_data["ogc_servers"][3]
        ogc_server.url = "config://mapserver"
        resp = test_app.get(f"/admin/ogc_servers/{ogc_server.id}/synchronize", status=200)

        resp = resp.forms["form-check"].submit("check")

        assert list(resp.html.find("div", class_="alert-success").stripped_strings) == [
            "OGC Server has been successfully synchronized."
        ]

    def test_dry_run_success(self, ogc_server_test_data, test_app):
        ogc_server = ogc_server_test_data["ogc_servers"][3]
        ogc_server.url = "config://mapserver"
        resp = test_app.get(f"/admin/ogc_servers/{ogc_server.id}/synchronize", status=200)

        resp = resp.forms["form-dry-run"].submit("dry-run")

        assert list(resp.html.find("div", class_="alert-success").stripped_strings) == [
            "OGC Server has been successfully synchronized."
        ]

    def test_synchronize_success(self, ogc_server_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import Log, LogAction

        ogc_server = ogc_server_test_data["ogc_servers"][3]
        ogc_server.url = "config://mapserver"
        resp = test_app.get(f"/admin/ogc_servers/{ogc_server.id}/synchronize", status=200)

        resp = resp.forms["form-synchronize"].submit("synchronize")

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.SYNCHRONIZE
        assert log.element_type == "ogc_server"
        assert log.element_id == ogc_server.id
        assert log.element_name == ogc_server.name
        assert log.username == "test_user"

        assert list(resp.html.find("div", class_="alert-success").stripped_strings) == [
            "OGC Server has been successfully synchronized."
        ]

        form = resp.forms["form-synchronize"]
        form["force-parents"].checked = True
        form["force-ordering"].checked = True
        form["clean"].checked = True

        resp = form.submit("synchronize")

        assert list(resp.html.find("div", class_="alert-success").stripped_strings) == [
            "OGC Server has been successfully synchronized."
        ]
