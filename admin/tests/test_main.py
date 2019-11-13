from pyramid import testing
import pytest
from webtest import TestApp as WebTestApp


@pytest.mark.usefixtures("app_env")
def test_main(app_env):
    """Test dev environment"""
    config = testing.setUp(registry=app_env["registry"])
    app = config.make_wsgi_app()
    testapp = WebTestApp(app)
    testapp.get("/admin/layertree/children", status=200)
