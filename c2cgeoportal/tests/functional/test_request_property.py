import base64
from nose.plugins.attrib import attr
from pyramid import testing
from unittest import TestCase

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule
)


@attr(functional=True)
@attr(request_property=True)
class TestRequestProperty(TestCase):

    def setUp(self):  # noqa
        self.config = testing.setUp()

        import transaction
        from c2cgeoportal.models import DBSession, User, Role

        r = Role(name=u'__test_role')
        u = User(
            username=u'__test_user', password=u'__test_user', role=r
        )

        DBSession.add(u)
        transaction.commit()

    def tearDown(self):  # noqa
        testing.tearDown()

        import transaction
        from c2cgeoportal.models import DBSession, User, Role

        transaction.commit()

        DBSession.query(User).filter_by(username=u'__test_user').delete()
        DBSession.query(Role).filter_by(name=u'__test_role').delete()
        transaction.commit()

    @attr(no_auth=True)
    def test_request_no_auth(self):
        request = self._create_request()
        self.assertEqual(request.user, None)

    @attr(auth=True)
    def test_request_auth(self):
        self.config.testing_securitypolicy(u'__test_user')
        request = self._create_request()
        self.assertEqual(request.user.username, u'__test_user')
        self.assertEqual(request.user.role.name, u'__test_role')

    @attr(right_auth=True)
    def test_request_right_auth(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal import get_user_from_request
        from c2cgeoportal import default_user_validator
        from c2cgeoportal.lib.authentication import create_authentication

        request = DummyRequest(headers={
            'Authorization': 'Basic ' + base64.b64encode('__test_user:__test_user').replace('\n', '')
        })
        request.registry.validate_user = default_user_validator
        request._get_authentication_policy = lambda: create_authentication({
            "authtkt_cookie_name": "__test",
            "authtkt_secret": "123",
        })
        request.set_property(
            get_user_from_request, name='user', reify=True
        )

        self.assertEqual(request.user.username, u'__test_user')

    @attr(wrong_auth=True)
    def test_request_wrong_auth(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal import get_user_from_request
        from c2cgeoportal import default_user_validator
        from c2cgeoportal.lib.authentication import create_authentication

        request = DummyRequest(headers={
            'Authorization': 'Basic ' + base64.b64encode('__test_user:__wrong_pass').replace('\n', '')
        })
        request.registry.validate_user = default_user_validator
        request._get_authentication_policy = lambda: create_authentication({
            "authtkt_cookie_name": "__test",
            "authtkt_secret": "123",
        })
        request.set_property(
            get_user_from_request, name='user', reify=True
        )

        self.assertEqual(request.user, None)

    def test_request_auth_overwritten_property(self):
        def setter(request):
            class User(object):
                pass

            class Role(object):
                pass

            u = User()
            u.username = u'__foo'
            u.role = Role()
            u.role.name = u'__bar'
            return u

        self.config.testing_securitypolicy(u'__test_user')
        request = self._create_request()
        request.set_property(setter, name='user', reify=True)
        self.assertEqual(request.user.username, u'__foo')
        self.assertEqual(request.user.role.name, u'__bar')

    def _create_request(self):
        from pyramid.request import Request
        from c2cgeoportal import get_user_from_request
        request = Request({})
        request.set_property(
            get_user_from_request, name='user'
        )
        return request
