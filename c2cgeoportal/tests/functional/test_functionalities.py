# -*- coding: utf-8 -*-

# Copyright (c) 2013-2017, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


from nose.plugins.attrib import attr
from unittest import TestCase

from c2cgeoportal.lib import functionality
from c2cgeoportal.tests.functional import (  # noqa
    tear_down_common as tearDownModule,
    set_up_common as setUpModule,
    create_default_ogcserver,
)


@attr(functional=True)
class TestFunctionalities(TestCase):

    @staticmethod
    def setUp():  # noqa
        import sqlahelper
        import transaction
        from c2cgeoportal.models import DBSession, Role, User, Functionality
        from c2cgeoportal.lib.dbreflection import init

        create_default_ogcserver()
        role1 = Role(name=u"__test_role1")
        user1 = User(
            username=u"__test_user1",
            password=u"__test_user1",
            role=role1
        )
        role2 = Role(name=u"__test_role2")
        user2 = User(
            username=u"__test_user2",
            password=u"__test_user2",
            role=role2
        )

        functionality1 = Functionality(u"__test_s", u"db")
        functionality2 = Functionality(u"__test_a", u"db1")
        functionality3 = Functionality(u"__test_a", u"db2")
        role2.functionalities = [functionality1, functionality2, functionality3]

        DBSession.add_all([user1, user2, role1, role2])
        transaction.commit()

        engine = sqlahelper.get_engine()
        init(engine)

    @staticmethod
    def tearDown():  # noqa
        import transaction
        from c2cgeoportal.models import DBSession, Role, User, Functionality, OGCServer

        functionality.FUNCTIONALITIES_TYPES = None

        transaction.commit()

        for o in DBSession.query(User).filter(
                User.username == "__test_user1").all():
            o.functionalities = []
            DBSession.delete(o)
        for o in DBSession.query(User).filter(
                User.username == "__test_user2").all():
            o.functionalities = []
            DBSession.delete(o)
        for o in DBSession.query(Role).filter(
                Role.name == "__test_role1").all():
            o.functionalities = []
            DBSession.delete(o)
        for o in DBSession.query(Role).filter(
                Role.name == "__test_role2").all():
            o.functionalities = []
            DBSession.delete(o)
        DBSession.query(Functionality).filter(
            Functionality.name == "__test_s").delete()
        DBSession.query(Functionality).filter(
            Functionality.name == "__test_a").delete()
        DBSession.query(Functionality).filter(
            Functionality.name == "__test_s").delete()
        DBSession.query(Functionality).filter(
            Functionality.name == "__test_a").delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()

    def test_functionalities(self):
        from c2cgeoportal.tests.functional import create_dummy_request
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.lib.functionality import get_functionality

        request = create_dummy_request()
        request.user = None
        request1 = create_dummy_request()
        request1.user = DBSession.query(User).filter(User.username == "__test_user1").one()
        request2 = create_dummy_request()
        request2.user = DBSession.query(User).filter(User.username == "__test_user2").one()

        settings = {
            "functionalities": {
                "anonymous": {},
                "registered": {},
            },
            "admin_interface": {
                "available_functionalities": ["__test_a", "__test_s"]
            }
        }
        functionality.FUNCTIONALITIES_TYPES = None
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
        self.assertEquals(get_functionality("__test_s", request), [])
        self.assertEquals(get_functionality("__test_a", request), [])
        self.assertEquals(get_functionality("__test_s", request1), [])
        self.assertEquals(get_functionality("__test_a", request1), [])
        self.assertEquals(get_functionality("__test_s", request2), ["db"])
        self.assertEquals(get_functionality("__test_a", request2), ["db1", "db2"])

        settings = {
            "functionalities": {
                "anonymous": {},
                "registered": {
                    "__test_s": "registered",
                    "__test_a": ["r1", "r2"]
                }
            },
            "admin_interface": {
                "available_functionalities": ["__test_a", "__test_s"]
            }
        }
        functionality.FUNCTIONALITIES_TYPES = None
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
        self.assertEquals(get_functionality("__test_s", request), [])
        self.assertEquals(get_functionality("__test_a", request), [])
        self.assertEquals(get_functionality("__test_s", request1), ["registered"])
        self.assertEquals(get_functionality("__test_a", request1), ["r1", "r2"])
        self.assertEquals(get_functionality("__test_s", request2), ["db"])
        self.assertEquals(get_functionality("__test_a", request2), ["db1", "db2"])

        settings = {
            "functionalities": {
                "anonymous": {
                    "__test_s": "anonymous",
                    "__test_a": ["a1", "a2"]
                },
                "registered": {}
            },
            "admin_interface": {
                "available_functionalities": ["__test_a", "__test_s"]
            }
        }
        functionality.FUNCTIONALITIES_TYPES = None
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
        self.assertEquals(get_functionality("__test_s", request), ["anonymous"])
        self.assertEquals(get_functionality("__test_a", request), ["a1", "a2"])
        self.assertEquals(get_functionality("__test_s", request1), ["anonymous"])
        self.assertEquals(get_functionality("__test_a", request1), ["a1", "a2"])
        self.assertEquals(get_functionality("__test_s", request2), ["db"])
        self.assertEquals(get_functionality("__test_a", request2), ["db1", "db2"])

        settings = {
            "functionalities": {
                "anonymous": {
                    "__test_s": "anonymous",
                    "__test_a": ["a1", "a2"]
                },
                "registered": {
                    "__test_s": "registered",
                    "__test_a": ["r1", "r2"]
                }
            },
            "admin_interface": {
                "available_functionalities": ["__test_a", "__test_s"]
            }
        }
        functionality.FUNCTIONALITIES_TYPES = None
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
        self.assertEquals(get_functionality("__test_s", request), ["anonymous"])
        self.assertEquals(get_functionality("__test_a", request), ["a1", "a2"])
        self.assertEquals(get_functionality("__test_s", request1), ["registered"])
        self.assertEquals(get_functionality("__test_a", request1), ["r1", "r2"])
        self.assertEquals(get_functionality("__test_s", request2), ["db"])
        self.assertEquals(get_functionality("__test_a", request2), ["db1", "db2"])

    def test_web_client_functionalities(self):
        from c2cgeoportal.models import DBSession, User
        from c2cgeoportal.tests.functional import create_dummy_request
        from c2cgeoportal.views.entry import Entry

        request = create_dummy_request()
        request.static_url = lambda url: "http://example.com/dummy/static/url"
        request1 = create_dummy_request()
        request1.static_url = lambda url: "http://example.com/dummy/static/url"
        request1.user = DBSession.query(User).filter(User.username == "__test_user1").one()
        request2 = create_dummy_request()
        request2.static_url = lambda url: "http://example.com/dummy/static/url"
        request2.user = DBSession.query(User).filter(User.username == "__test_user2").one()

        settings = {
            "functionalities": {
                "anonymous": {
                    "__test_s": "anonymous",
                    "__test_a": ["a1", "a2"]
                },
                "registered": {
                    "__test_s": "registered",
                    "__test_a": ["r1", "r2"]
                },
                "available_in_templates": ["__test_s", "__test_a"],
            },
            "admin_interface": {
                "available_functionalities": ["__test_a", "__test_s"]
            },
        }
        functionality.FUNCTIONALITIES_TYPES = None
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)

        annon = Entry(request).get_cgxp_viewer_vars()
        u1 = Entry(request1).get_cgxp_viewer_vars()
        u2 = Entry(request2).get_cgxp_viewer_vars()
        self.assertEquals(annon["functionality"], {"__test_s": ["anonymous"], "__test_a": ["a1", "a2"]})
        self.assertEquals(u1["functionality"], {"__test_s": ["registered"], "__test_a": ["r1", "r2"]})
        self.assertEquals(u2["functionality"], {"__test_s": ["db"], "__test_a": ["db1", "db2"]})
