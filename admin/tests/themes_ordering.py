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
