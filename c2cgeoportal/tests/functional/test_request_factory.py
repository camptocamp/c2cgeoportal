from nose.plugins.attrib import attr
from pyramid import testing
from unittest import TestCase

from c2cgeoportal.tests.functional import tearDownModule, setUpModule


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

        self.config.testing_securitypolicy(u'__test_user')

    def tearDown(self):
        testing.tearDown()

        import transaction
        from c2cgeoportal.models import DBSession, User, Role

        transaction.commit()

        DBSession.query(User).filter_by(username=u'__test_user').delete()
        DBSession.query(Role).filter_by(name=u'__test_role').delete()
        transaction.commit()

    def test_request(self):
        from c2cgeoportal import Request
        request = Request({})
        # we do the same assertion twice, to verify that
        # reify works for us
        self.assertEqual(request.user.username, u'__test_user')
        self.assertEqual(request.user.username, u'__test_user')
