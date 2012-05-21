from nose.plugins.attrib import attr
from pyramid import testing
from unittest import TestCase

from c2cgeoportal.tests.functional import (tearDownModule,  # NOQA
                                           setUpModule)  # NOQA


@attr(functional=True)
class TestRequestFactory(TestCase):

    def setUp(self):
        self.config = testing.setUp()

        import transaction
        from c2cgeoportal.models import DBSession, User, Role

        r = Role(name=u'__test_role')
        u = User(username=u'__test_user', password=u'__test_user',
                 role=r
                 )

        DBSession.add(u)
        transaction.commit()

    def tearDown(self):
        testing.tearDown()

        import transaction
        from c2cgeoportal.models import DBSession, User, Role

        transaction.commit()

        DBSession.query(User).filter_by(username=u'__test_user').delete()
        DBSession.query(Role).filter_by(name=u'__test_role').delete()
        transaction.commit()

    def test_request_no_auth(self):
        request = self._create_request()
        # we do the same assertion twice, to verify that
        # reify works for us
        self.assertEqual(request.user, None)
        self.assertEqual(request.user, None)

    def test_request_auth(self):
        self.config.testing_securitypolicy(u'__test_user')
        request = self._create_request()
        # we do the same assertion twice, to verify that
        # reify works for us
        self.assertEqual(request.user.username, u'__test_user')
        self.assertEqual(request.user.username, u'__test_user')

    def test_request_auth_overwritten_property(self):
        def setter(request):
            class User(object):
                pass
            u = User()
            u.username = u'__foo'
            return u

        self.config.testing_securitypolicy(u'__test_user')
        request = self._create_request()
        request.set_property(setter, name='user', reify=True)
        # we do the same assertion twice, to verify that
        # reify works for us
        self.assertEqual(request.user.username, u'__foo')
        self.assertEqual(request.user.username, u'__foo')

    def _create_request(self):
        from pyramid.request import Request
        from c2cgeoportal import get_user_from_request
        request = Request({})
        request.set_property(get_user_from_request,
                             name='user', reify=True)
        return request
