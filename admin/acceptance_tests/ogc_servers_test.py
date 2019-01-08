# pylint: disable=no-self-use

import pytest
import re

from . import AbstractViewsTests


@pytest.fixture(scope='function')
@pytest.mark.usefixtures('dbsession', 'transact')
def ogc_server_test_data(dbsession, transact):
    del transact

    from c2cgeoportal_commons.models.main import OGCServer

    auth = ['No auth', 'Standard auth', 'Geoserver auth', 'Proxy']
    servers = []
    for i in range(0, 8):
        server = OGCServer(
            name='server_{}'.format(i),
            description='description_{}'.format(i))
        server.url = 'https://somebasicurl_{}.com'.format(i)
        server.image_type = 'image/jpeg' if i % 2 == 0 else 'image/png'
        server.auth = auth[i % 4]
        dbsession.add(server)
        servers.append(server)

    dbsession.flush()

    yield {
        'ogc_servers': servers
    }


@pytest.mark.usefixtures('ogc_server_test_data', 'test_app')
class TestOGCServer(AbstractViewsTests):

    _prefix = '/ogc_servers'

    def test_index_rendering(self, test_app):
        resp = self.get(test_app)

        self.check_left_menu(resp, 'OGC Servers')

        expected = [('actions', '', 'false'),
                    ('id', 'id', 'true'),
                    ('name', 'Name', 'true'),
                    ('description', 'Description', 'true'),
                    ('url', 'Basic URL', 'true'),
                    ('url_wfs', 'WFS URL', 'true'),
                    ('type', 'Server type', 'true'),
                    ('image_type', 'Image type', 'true'),
                    ('auth', 'Authentication type', 'true'),
                    ('wfs_support', 'WFS support', 'true'),
                    ('is_single_tile', 'Single tile', 'true')]
        self.check_grid_headers(resp, expected)

    def test_grid_search(self, test_app):
        # search on ogc_server name
        self.check_search(test_app, 'server_0', total=1)

    def test_submit_new(self, dbsession, test_app):
        from c2cgeoportal_commons.models.main import OGCServer
        resp = test_app.post(
            '/ogc_servers/new',
            {
                'name': 'new_name',
                'description': 'new description',
                'url': 'www.randomurl.com',
                'type': 'mapserver',
                'auth': 'No auth',
                'image_type': 'image/png'
            },
            status=302)
        ogc_server = dbsession.query(OGCServer). \
            filter(OGCServer.name == 'new_name'). \
            one()
        assert str(ogc_server.id) == re.match(
            r'http://localhost/ogc_servers/(.*)\?msg_col=submit_ok',
            resp.location
        ).group(1)
        assert ogc_server.name == 'new_name'

    def test_edit(self, test_app, ogc_server_test_data):
        ogc_server = ogc_server_test_data['ogc_servers'][0]
        resp = test_app.get('/ogc_servers/{}'.format(ogc_server.id), status=200)
        form = resp.form
        assert str(ogc_server.id) == self.get_first_field_named(form, 'id').value
        assert 'hidden' == self.get_first_field_named(form, 'id').attrs['type']
        assert ogc_server.name == form['name'].value
        form['description'] = 'new_description'
        assert form.submit().status_int == 302
        assert ogc_server.description == 'new_description'

    def test_delete(self, test_app, ogc_server_test_data, dbsession):
        from c2cgeoportal_commons.models.main import OGCServer

        ogc_server = ogc_server_test_data['ogc_servers'][0]
        deleted_id = ogc_server.id
        test_app.delete('/ogc_servers/{}'.format(deleted_id), status=200)
        assert dbsession.query(OGCServer).get(deleted_id) is None

    def test_duplicate(self, ogc_server_test_data, test_app, dbsession):
        from c2cgeoportal_commons.models.main import OGCServer
        ogc_server = ogc_server_test_data['ogc_servers'][3]
        resp = test_app.get("/ogc_servers/{}/duplicate".format(ogc_server.id), status=200)
        form = resp.form
        assert '' == self.get_first_field_named(form, 'id').value
        self.set_first_field_named(form, 'name', 'clone')
        resp = form.submit('submit')
        assert resp.status_int == 302
        server = dbsession.query(OGCServer). \
            filter(OGCServer.name == 'clone'). \
            one()
        assert str(server.id) == re.match(
            r'http://localhost/ogc_servers/(.*)\?msg_col=submit_ok',
            resp.location
        ).group(1)

    def test_unicity_validator(self, ogc_server_test_data, test_app):
        ogc_server = ogc_server_test_data['ogc_servers'][3]
        resp = test_app.get("/ogc_servers/{}/duplicate".format(ogc_server.id), status=200)

        resp = resp.form.submit('submit')

        self._check_submission_problem(resp, '{} is already used.'.format(ogc_server.name))
