import pytest

from . import AbstractViewsTests


@pytest.mark.usefixtures("test_app")
class TestHome(AbstractViewsTests):
    _prefix = "/admin/"

    def test_index_rendering(self, test_app) -> None:
        resp = self.get(test_app, status=302)
        assert resp.location == "http://localhost/admin/layertree"
        to_layer_tree = resp.follow()
        assert to_layer_tree.html.select_one('div[id="layertree"]') is not None
