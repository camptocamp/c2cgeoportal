# pylint: disable=no-self-use

import email
import re
from unittest.mock import MagicMock, patch

import pyramid.httpexceptions
import pytest
from pyramid.testing import DummyRequest

from . import AbstractViewsTests


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def users_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Role
    from c2cgeoportal_commons.models.static import User

    roles = []
    for i in range(0, 4):
        roles.append(Role(f"secretary_{i}"))
        dbsession.add(roles[i])
    users = []
    for i in range(0, 23):
        user = User(
            f"babar_{i}",
            email=f"mail{i}@valid.net",
            settings_role=roles[i % 4],
            roles=[roles[i % 4]],
        )
        user.password = "pré$ident"
        user.is_password_changed = i % 2 == 1
        users.append(user)
        dbsession.add(user)

    dbsession.flush()

    yield {"roles": roles, "users": users}


EXPECTED_WELCOME_MAIL = (
    "Hello {},\n\nYou have a new account on GeoMapFish demo: https://geomapfish-demo.camptocamp.com/2.3\n"
    + "Your user name is: {}\nYour password is: {}\n\nSincerely yours\nThe GeoMapFish team\n"
)


@pytest.mark.usefixtures("users_test_data", "test_app")
class TestUser(AbstractViewsTests):
    _prefix = "/admin/users"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "Users")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("username", "Username"),
            ("display_name", "Display name", "true"),
            ("email", "Email"),
            ("last_login", "Last login"),
            ("expire_on", "Expiration date"),
            ("deactivated", "Deactivated"),
            ("settings_role", "Settings role"),
            ("roles", "Roles", "false"),
        ]

        self.check_grid_headers(resp, expected)

    @pytest.mark.skip(reason="Translations seems not available in tests")
    def test_index_rendering_fr(self, test_app):
        resp = self.get(test_app, locale="fr")

        self.check_left_menu(resp, "Utilisateurs")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("username", "Nom d'utilisateur"),
            ("email", "Email"),
            ("last_login", "Dernière connection"),
            ("expire_on", "Date d'expiration"),
            ("deactivated", "Désactivé"),
            ("settings_role", "Rôle de configuration"),
            ("roles", "Rôles", "false"),
        ]
        self.check_grid_headers(resp, expected, new="Nouveau")

    def test_view_edit(self, test_app, users_test_data, dbsession):
        from c2cgeoportal_commons.models.main import LogAction
        from c2cgeoportal_commons.models.static import Log

        user = users_test_data["users"][9]
        roles = users_test_data["roles"]

        resp = test_app.get(f"/admin/users/{user.id}", status=200)

        assert resp.form["username"].value == user.username
        assert resp.form["email"].value == user.email
        assert resp.form["settings_role_id"].options == [("", False, "- Select -")] + [
            (str(role.id), role.name == "secretary_1", role.name) for role in roles
        ]
        assert resp.form["settings_role_id"].value == str(user.settings_role_id)
        self._check_roles(resp.form, roles, user)

        assert user.roles == [roles[1]]

        new_values = {
            "username": "new_name",
            "email": "new_email@domain.com",
            "settings_role_id": roles[2].id,
        }
        for key, value in new_values.items():
            self.set_first_field_named(resp.form, key, value)
        resp.form["roles"] = [roles[2].id, roles[3].id]
        resp.form.submit("submit")

        for key, value in new_values.items():
            if isinstance(value, bool):
                assert value == getattr(user, key)
            else:
                assert str(value or "") == str(getattr(user, key) or "")
        assert {roles[2].id, roles[3].id} == {role.id for role in user.roles}

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.UPDATE
        assert log.element_type == "user"
        assert log.element_id == user.id
        assert log.element_name == user.username
        assert log.username == "test_user"

    def test_delete(self, test_app, users_test_data, dbsession):
        from c2cgeoportal_commons.models.main import LogAction
        from c2cgeoportal_commons.models.static import Log, User, user_role

        user = users_test_data["users"][9]
        deleted_id = user.id
        test_app.delete(f"/admin/users/{deleted_id}", status=200)
        assert dbsession.query(User).get(deleted_id) is None
        assert dbsession.query(user_role).filter(user_role.c.user_id == user.id).count() == 0

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.DELETE
        assert log.element_type == "user"
        assert log.element_id == user.id
        assert log.element_name == user.username
        assert log.username == "test_user"

    @patch("c2cgeoportal_commons.lib.email_.smtplib.SMTP")
    @patch("c2cgeoportal_admin.views.users.pwgenerator.generate")
    def test_submit_update(self, pw_gen_mock, smtp_mock, dbsession, test_app, users_test_data):
        user = users_test_data["users"][11]
        roles = users_test_data["roles"]

        resp = test_app.post(
            f"/admin/users/{user.id}",
            (
                ("__formid__", "deform"),
                ("_charset_", "UTF-8"),
                ("formsubmit", "formsubmit"),
                ("item_type", "user"),
                ("id", user.id),
                ("username", "new_name_withéàô"),
                ("display_name", "New name withéàô"),
                ("email", "new_mail@valid.net"),
                ("settings_role_id", roles[2].id),
                ("__start__", "roles:sequence"),
                ("roles", roles[0].id),
                ("roles", roles[3].id),
                ("__end__", "roles:sequence"),
            ),
            status=302,
        )
        assert resp.location == f"http://localhost/admin/users/{user.id}?msg_col=submit_ok"

        dbsession.expire(user)
        assert user.username == "new_name_withéàô"
        assert user.email == "new_mail@valid.net"
        assert user.settings_role.name == "secretary_2"
        assert {r.id for r in user.roles} == {roles[i].id for i in [0, 3]}
        assert user.validate_password("pré$ident")

        assert not pw_gen_mock.called, "method should not have been called"
        assert not smtp_mock.called, "method should not have been called"

    def test_unicity_validator(self, users_test_data, test_app):
        user = users_test_data["users"][11]
        roles = users_test_data["roles"]

        resp = test_app.post(
            f"/admin/users/{user.id}",
            {
                "__formid__": "deform",
                "_charset_": "UTF-8",
                "formsubmit": "formsubmit",
                "item_type": "user",
                "id": user.id,
                "username": "babar_0",
                "email": "new_mail",
                "settings_role_id": roles[2].id,
            },
            status=200,
        )

        self._check_submission_problem(resp, "{} is already used.".format("babar_0"))

    @patch("c2cgeoportal_commons.lib.email_.smtplib.SMTP")
    @patch("c2cgeoportal_admin.views.users.pwgenerator.generate")
    def test_duplicate(self, pw_gen_mock, smtp_mock, users_test_data, test_app, dbsession):
        sender_mock = MagicMock()
        smtp_mock.return_value.__enter__.return_value = sender_mock
        pw_gen_mock.return_value = "basile"
        from c2cgeoportal_commons.models.static import User

        user = users_test_data["users"][7]
        roles = users_test_data["roles"]

        resp = test_app.get(f"/admin/users/{user.id}/duplicate", status=200)
        form = resp.form

        assert "" == form["id"].value
        assert user.username == form["username"].value
        assert user.email == form["email"].value
        assert str(user.settings_role_id) == form["settings_role_id"].value
        self._check_roles(resp.form, roles, user)
        assert user.is_password_changed

        form["username"].value = "clone"
        resp = form.submit("submit", status=302)

        new_user = dbsession.query(User).filter(User.username == "clone").one()

        assert str(new_user.id) == re.match(
            r"http://localhost/admin/users/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)
        assert user.id != new_user.id
        assert user.settings_role_id == new_user.settings_role_id
        assert {role.id for role in user.roles} == {role.id for role in new_user.roles}
        assert not new_user.is_password_changed
        assert not new_user.validate_password("pré$ident")

        parts = list(email.message_from_string(sender_mock.sendmail.mock_calls[0][1][2]).walk())
        assert EXPECTED_WELCOME_MAIL.format("clone", "clone", "basile") == parts[1].get_payload(
            decode=True
        ).decode("utf8")
        assert "mail7@valid.net" == parts[0].items()[3][1]

    @patch("c2cgeoportal_commons.lib.email_.smtplib.SMTP")
    @patch("c2cgeoportal_admin.views.users.pwgenerator.generate")
    @pytest.mark.usefixtures("test_app")
    def test_submit_new(self, pw_gen_mock, smtp_mock, dbsession, test_app, users_test_data):
        from c2cgeoportal_commons.models.main import LogAction
        from c2cgeoportal_commons.models.static import Log, User

        sender_mock = MagicMock()
        smtp_mock.return_value.__enter__.return_value = sender_mock
        pw_gen_mock.return_value = "basile"

        roles = users_test_data["roles"]

        resp = test_app.post(
            "/admin/users/new",
            (
                ("__formid__", "deform"),
                ("_charset_", "UTF-8"),
                ("formsubmit", "formsubmit"),
                ("item_type", "user"),
                ("id", ""),
                ("username", "new_user"),
                ("display_name", "New user"),
                ("email", "valid@email.net"),
                ("settings_role_id", roles[2].id),
            ),
            status=302,
        )

        user = dbsession.query(User).filter(User.username == "new_user").one()

        assert str(user.id) == re.match(
            r"http://localhost/admin/users/(.*)\?msg_col=submit_ok", resp.location
        ).group(1)

        assert user.username == "new_user"
        assert user.display_name == "New user"
        assert user.email == "valid@email.net"
        assert user.settings_role_id == roles[2].id
        assert user.password is not None and len(user.password)
        assert user.password.startswith("$")
        assert user.temp_password is None
        assert user.is_password_changed is False

        parts = list(email.message_from_string(sender_mock.sendmail.mock_calls[0][1][2]).walk())
        assert EXPECTED_WELCOME_MAIL.format("new_user", "new_user", "basile") == parts[1].get_payload(
            decode=True
        ).decode("utf8")
        assert "valid@email.net" == parts[0].items()[3][1]

        log = dbsession.query(Log).one()
        assert log.date != None
        assert log.action == LogAction.INSERT
        assert log.element_type == "user"
        assert log.element_id == user.id
        assert log.element_name == user.username
        assert log.username == "test_user"

    def test_invalid_email(self, test_app):
        resp = test_app.post(
            "/admin/users/new",
            {
                "__formid__": "deform",
                "_charset_": "UTF-8",
                "formsubmit": "formsubmit",
                "item_type": "user",
                "id": "",
                "username": "invalid_email",
                "display_name": "Invalid email",
                "email": "new_mail",
                "role_name": "secretary_2",
                "is_password_changed": "false",
                "_password": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
                "temp_password": "",
            },
            status=200,
        )
        self._check_submission_problem(resp, "Invalid email address")

    @pytest.mark.usefixtures("raise_db_error_on_query")
    def test_grid_dberror(self, dbsession):
        from c2cgeoportal_admin.views.users import UserViews

        request = DummyRequest(dbsession=dbsession, params={"offset": 0, "limit": 10})
        with pytest.raises(pyramid.httpexceptions.HTTPInternalServerError):
            UserViews(request).grid()

    def test_grid_settings_role_none(self, dbsession, test_app):
        """
        Grid view must work even if a user's settings_role is None.
        """
        from c2cgeoportal_commons.models.static import User

        dbsession.add(User("test", email="test@valid.net"))
        self.check_search(test_app, "test", total=1)
