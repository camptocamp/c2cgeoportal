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


# pylint: disable=no-self-use

import pytest

from . import AbstractViewsTests


@pytest.fixture
def left_menu_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Role

    roles = []
    role = Role("secretary")
    dbsession.add(role)
    roles.append(role)

    dbsession.flush()

    return {"roles": roles}


@pytest.mark.usefixtures("test_app")
class TestLeftMenu(AbstractViewsTests):
    _prefix = "/admin/roles"

    def test_index(self, test_app) -> None:
        resp = test_app.get("/admin/roles", status=200)
        self.check_left_menu(resp, "Roles")

    @pytest.mark.usefixtures("left_menu_test_data")
    def test_edit(self, test_app, left_menu_test_data) -> None:
        role = left_menu_test_data["roles"][0]
        resp = self.get_item(test_app, role.id)
        self.check_left_menu(resp, "Roles")
