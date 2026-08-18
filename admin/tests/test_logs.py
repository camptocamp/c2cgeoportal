# Copyright (c) 2025-2026, Camptocamp SA
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


# pylint: disable=no-self-use,unsubscriptable-object

import datetime

import pytest

from . import AbstractViewsTests


@pytest.fixture
def logs_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Log as MainLog
    from c2cgeoportal_commons.models.main import LogAction
    from c2cgeoportal_commons.models.static import Log as StaticLog

    logs = []
    for i in range(5):
        log = MainLog(
            date=datetime.datetime.now(datetime.UTC),
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
            date=datetime.datetime.now(datetime.UTC),
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

    return {
        "logs": logs,
    }


@pytest.mark.usefixtures("logs_test_data", "test_app")
class TestLog(AbstractViewsTests):
    _prefix = "/admin/logs"

    def test_index_rendering(self, test_app) -> None:
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

    def test_grid_default_sort_on_date_desc(self, test_app, logs_test_data) -> None:
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

    def test_grid_sort_on_element_type(self, test_app, logs_test_data) -> None:
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

    def test_grid_search(self, test_app) -> None:
        self.check_search(test_app, "role", total=5)
        self.check_search(test_app, "user_2", total=1)
