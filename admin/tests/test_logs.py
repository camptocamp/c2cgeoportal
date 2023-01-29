# pylint: disable=no-self-use,unsubscriptable-object

import datetime
import json
import re

import pytest
import pytz
from pyramid.testing import DummyRequest

from . import AbstractViewsTests


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def logs_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import AbstractLog, Log as MainLog, LogAction
    from c2cgeoportal_commons.models.static import Log as StaticLog

    logs = []
    for i in range(0, 5):
        log = MainLog(
            date=datetime.datetime.now(pytz.utc),
            action=[LogAction.INSERT, LogAction.UPDATE, LogAction.DELETE][i % 3],
            element_type="role",
            element_id=i,
            username="testuser",
        )
        dbsession.add(log)
        logs.append(log)

        log = StaticLog(
            date=datetime.datetime.now(pytz.utc),
            action=[LogAction.INSERT, LogAction.UPDATE, LogAction.DELETE][i % 3],
            element_type="user",
            element_id=i,
            username="testuser",
        )
        dbsession.add(log)
        logs.append(log)

    dbsession.flush()

    yield {
        "logs": logs,
    }


@pytest.mark.usefixtures("logs_test_data", "test_app")
class TestLog(AbstractViewsTests):

    _prefix = "/admin/logs"

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, "Logs")

        expected = [
            ("actions", "", "false"),
            ("id", "id", "true"),
            ("date", "Date"),
            ("action", "Action"),
            ("element_type", "Element type"),
            ("element_id", "Element identifier"),
            ("username", "Username"),
        ]
        self.check_grid_headers(resp, expected, new=False)

    def test_grid_sort_on_element_type(self, test_app, logs_test_data):
        json = self.check_search(test_app, sort="element_type")
        for i, log in enumerate(
            sorted(logs_test_data["logs"], key=lambda log: (log.element_type, log.id))
        ):
            if i == 10:
                break
            assert str(log.id) == json["rows"][i]["_id_"]

    def test_grid_search(self, test_app):
        self.check_search(test_app, "role", total=5)
