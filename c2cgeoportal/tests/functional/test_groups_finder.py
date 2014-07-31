from nose.plugins.attrib import attr
from pyramid import testing
from unittest import TestCase

from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule
)


@attr(functional=True)
class TestGroupsFinder(TestCase):

    def setUp(self):  # noqa
        self.config = testing.setUp()

        import transaction
        from c2cgeoportal.models import DBSession, User, Role

        r = Role(name=u'__test_role')
        u = User(username=u'__test_user', password=u'__test_user',
                 role=r
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

    @attr(group_finder=True)
    def test_it(self):
        from c2cgeoportal.resources import defaultgroupsfinder
        self.config.testing_securitypolicy(u'__test_user')
        request = self._create_request()
        roles = defaultgroupsfinder(u'__test_user', request)
        self.assertEqual(roles, [u'__test_role'])

    def _create_request(self):
        from pyramid.request import Request
        from c2cgeoportal import get_user_from_request
        request = Request({})
        request.set_property(get_user_from_request,
                             name='user', reify=True)
        return request
