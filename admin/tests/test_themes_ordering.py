# pylint: disable=no-self-use

import pytest

from .test_treegroup import TestTreeGroup


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("dbsession", "transact")
def theme_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import Theme

    themes = []
    for i in range(0, 3):
        theme = Theme(name="theme_{}".format(i), ordering=i, icon="icon_{}".format(i))

        dbsession.add(theme)
        themes.append(theme)

    dbsession.flush()

    yield {
        "themes": themes,
    }


@pytest.mark.usefixtures("theme_test_data", "test_app")
class TestThemeOrdering(TestTreeGroup):

    _prefix = "/admin/layertree/ordering"

    def test_edit(self, test_app, theme_test_data, dbsession):
        themes = theme_test_data["themes"]

        resp = test_app.get(self._prefix, status=200)
        form = resp.form

        self.check_children(
            form,
            "themes",
            [
                {"label": theme.name, "values": {"id": str(theme.id), "ordering": str(theme.ordering)}}
                for theme in themes
            ],
        )

    def test_save(self, test_app, theme_test_data, dbsession):
        themes = theme_test_data["themes"]

        resp = test_app.post(
            self._prefix,
            (
                ("_charset_", "UTF-8"),
                ("__formid__", "deform"),
                ("__start__", "themes:sequence"),
                ("__start__", "theme:mapping"),
                ("id", themes[0].id),
                ("ordering", ""),
                ("__end__", "theme:mapping"),
                ("__start__", "theme:mapping"),
                ("id", themes[2].id),
                ("ordering", ""),
                ("__end__", "theme:mapping"),
                ("__start__", "theme:mapping"),
                ("id", themes[1].id),
                ("ordering", ""),
                ("__end__", "theme:mapping"),
                ("__end__", "themes:sequence"),
                ("formsubmit", "formsubmit"),
            ),
            status=302,
        )

        assert resp.location == "http://localhost/admin/layertree"

        assert themes[0].ordering == 0
        assert themes[2].ordering == 1
        assert themes[1].ordering == 2
