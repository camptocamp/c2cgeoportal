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

from .test_treegroup import TestTreeGroup


@pytest.fixture
def themes_ordering_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Theme

    themes = []
    for i in range(25):
        theme = Theme(name=f"theme_{i}", ordering=100)
        dbsession.add(theme)
        themes.append(theme)

    dbsession.flush()

    return {"themes": themes}


@pytest.mark.usefixtures("themes_ordering_test_data", "test_app")
class TestThemesOrdering(TestTreeGroup):
    _prefix = "/admin/layertree/ordering"

    def test_edit(self, test_app, themes_ordering_test_data) -> None:
        resp = self.get(test_app, status=200)
        form = resp.form

        self.check_children(
            form,
            "themes",
            [
                {"label": theme.name, "values": {"id": str(theme.id)}}
                for theme in sorted(themes_ordering_test_data["themes"], key=lambda t: (t.ordering, t.name))
            ],
        )

        resp = form.submit("submit", status=302)
        assert resp.location == "http://localhost/admin/layertree"

        for i, theme in enumerate(sorted(themes_ordering_test_data["themes"], key=lambda t: t.name)):
            assert i == theme.ordering
