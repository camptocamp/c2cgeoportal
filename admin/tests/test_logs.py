# pylint: disable=no-self-use,unsubscriptable-object

import datetime
from datetime import timezone

import pytest

from . import AbstractViewsTests


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def logs_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import AbstractLog
    from c2cgeoportal_commons.models.main import Log as MainLog
    from c2cgeoportal_commons.models.main import LogAction
    from c2cgeoportal_commons.models.static import Log as StaticLog

    logs = []
    for i in range(0, 5):
        log = MainLog(
            date=datetime.datetime.now(timezone.utc),
            action=[LogAction.INSERT, LogAction.UPDATE, LogAction.DELETE][i % 3],
            element_type="role",
            element_id=i,
            element_name=f"role_{i}",
            element_url_table="roles",
            username="testuser",
        )
        dbsession.add(log)
        logs.append(log)

        log = StaticLog(
            date=datetime.datetime.now(timezone.utc),
            action=[LogAction.INSERT, LogAction.UPDATE, LogAction.DELETE][i % 3],
            element_type="user",
            element_id=i,
            element_name=f"user_{i}",
            element_url_table="users",
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
            ("username", "Username"),
            ("action", "Action"),
            ("element_type", "Element type"),
            ("element_id", "Element identifier"),
            ("element_name", "Element name"),
        ]
        self.check_grid_headers(resp, expected, new=False)

    def test_grid_default_sort_on_date_desc(self, test_app, logs_test_data):
        json = self.check_search(test_app)
        expected_ids = [
            log.id
            for log in sorted(
                logs_test_data["logs"],
                key=lambda log: log.date,
                reverse=True,
            )
        ]
        result_ids = [int(row["_id_"]) for row in json["rows"]]
        assert result_ids == expected_ids

    def test_grid_sort_on_element_type(self, test_app, logs_test_data):
        json = self.check_search(test_app, sort="element_type")
        expected_ids = [
            log.id
            for log in sorted(
                logs_test_data["logs"],
                key=lambda log: (log.element_type, -log.date.timestamp()),
            )
        ]
        result_ids = [int(row["_id_"]) for row in json["rows"]]
        assert result_ids == expected_ids

    def test_grid_search(self, test_app):
        self.check_search(test_app, "role", total=5)
        self.check_search(test_app, "user_2", total=1)
