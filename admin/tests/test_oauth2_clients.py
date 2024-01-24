# pylint: disable=no-self-use,unsubscriptable-object

import re
from uuid import uuid4

import pyramid.httpexceptions
import pytest
from pyramid.testing import DummyRequest

from .test_treegroup import TestTreeGroup


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def oauth2_clients_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.static import OAuth2Client

    clients = []
    for i in range(23):
        client = OAuth2Client()
        client.client_id = str(uuid4())
        client.secret = "1234"
        client.redirect_uri = "http://127.0.0.1:7070/"

        dbsession.add(client)
        clients.append(client)

    dbsession.flush()

    yield {
        "oauth2_clients": clients,
    }


@pytest.mark.usefixtures("oauth2_clients_test_data", "test_app")
class TestOAuth2Client(TestTreeGroup):
    _prefix = "/admin/oauth2_clients"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "OAuth2 Clients")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("client_id", "Client ID"),
            ("secret", "Secret"),
            ("redirect_uri", "Redirect URI"),
        ]
        self.check_grid_headers(resp, expected)

    def test_grid_search(self, test_app, oauth2_clients_test_data):
        self.check_search(test_app, "", total=23)

        client = oauth2_clients_test_data["oauth2_clients"][0]
        self.check_search(test_app, client.client_id, total=1)

    def test_submit_new(self, dbsession, test_app, oauth2_clients_test_data):
        from c2cgeoportal_commons.models.main import LogAction
        from c2cgeoportal_commons.models.static import Log, OAuth2Client

        resp = test_app.post(
            "/admin/oauth2_clients/new",
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("id", ""),
                ("client_id", "qgis2"),
                ("secret", "12345"),
                ("redirect_uri", "http://127.0.0.1:7070/bis"),
                ("formsubmit", "formsubmit"),
            ),
            status=302,
        )

        oauth2_client = dbsession.query(OAuth2Client).filter(OAuth2Client.client_id == "qgis2").one()
        assert str(oauth2_client.id) == re.match(
            r"http://localhost/admin/oauth2_clients/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

        assert oauth2_client.client_id == "qgis2"
        assert oauth2_client.secret == "12345"
        assert oauth2_client.redirect_uri == "http://127.0.0.1:7070/bis"

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.INSERT
        assert log.element_type == "oauth2_client"
        assert log.element_id == oauth2_client.id
        assert log.element_name == oauth2_client.client_id
        assert log.username == "test_user"

    def test_edit_then_save(self, dbsession, test_app, oauth2_clients_test_data):
        from c2cgeoportal_commons.models.main import LogAction
        from c2cgeoportal_commons.models.static import Log

        oauth2_client = oauth2_clients_test_data["oauth2_clients"][10]

        dbsession.expire(oauth2_client)

        form = self.get_item(test_app, oauth2_client.id).form

        assert str(oauth2_client.id) == form["id"].value
        assert oauth2_client.client_id == form["client_id"].value
        assert oauth2_client.secret == form["secret"].value
        assert oauth2_client.redirect_uri == form["redirect_uri"].value

        form["client_id"] = "New client ID"
        form["secret"] = "New secret"
        form["redirect_uri"] = "New redirect URI"

        resp = form.submit("submit")

        assert str(oauth2_client.id) == re.match(
            r"http://localhost/admin/oauth2_clients/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

        dbsession.expire(oauth2_client)

        assert "New client ID" == oauth2_client.client_id
        assert "New secret" == oauth2_client.secret
        assert "New redirect URI" == oauth2_client.redirect_uri

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.UPDATE
        assert log.element_type == "oauth2_client"
        assert log.element_id == oauth2_client.id
        assert log.element_name == oauth2_client.client_id
        assert log.username == "test_user"

    def test_duplicate(self, oauth2_clients_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.static import OAuth2Client

        oauth2_client_proto = oauth2_clients_test_data["oauth2_clients"][7]

        resp = test_app.get(f"/admin/oauth2_clients/{oauth2_client_proto.id}/duplicate", status=200)
        form = resp.form

        assert "" == self.get_first_field_named(form, "id").value
        assert oauth2_client_proto.client_id == form["client_id"].value
        assert oauth2_client_proto.secret == form["secret"].value
        assert oauth2_client_proto.redirect_uri == form["redirect_uri"].value
        form["client_id"].value = "clone"
        resp = form.submit("submit")

        oauth2_client = dbsession.query(OAuth2Client).filter(OAuth2Client.client_id == "clone").one()
        assert str(oauth2_client.id) == re.match(
            r"http://localhost/admin/oauth2_clients/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
        assert oauth2_client_proto.id != oauth2_client.id

    def test_delete(self, test_app, dbsession):
        from c2cgeoportal_commons.models.main import LogAction
        from c2cgeoportal_commons.models.static import Log, OAuth2Client

        oauth2_client = dbsession.query(OAuth2Client).first()
        test_app.delete(f"/admin/oauth2_clients/{oauth2_client.id}", status=200)
        assert dbsession.query(OAuth2Client).get(oauth2_client.id) is None

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.DELETE
        assert log.element_type == "oauth2_client"
        assert log.element_id == oauth2_client.id
        assert log.element_name == oauth2_client.client_id
        assert log.username == "test_user"

    def test_unicity_validator(self, oauth2_clients_test_data, test_app):
        oauth2_client_proto = oauth2_clients_test_data["oauth2_clients"][7]
        resp = test_app.get(f"/admin/oauth2_clients/{oauth2_client_proto.id}/duplicate", status=200)

        resp = resp.form.submit("submit")

        self._check_submission_problem(resp, f"{oauth2_client_proto.client_id} is already used.")

    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.oauth2_clients import OAuth2ClientViews

        request = DummyRequest(dbsession=dbsession, params={"offset": 0, "limit": 10})
        with pytest.raises(pyramid.httpexceptions.HTTPInternalServerError):
            OAuth2ClientViews(request).grid()
