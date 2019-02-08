import pytest
from pyramid import testing
from webtest import TestApp as WebTestApp


@pytest.mark.usefixtures('app_env')
def test_main(app_env):
    """Test dev environment"""
    config = testing.setUp(registry=app_env['registry'])
    app = config.make_wsgi_app()
    testapp = WebTestApp(app)
    testapp.get('/layertree/children', status=200)
