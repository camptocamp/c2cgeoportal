# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
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

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


from unittest import TestCase

from tests.functional import create_default_ogcserver, fill_tech_user_functionality
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestFunctionalities(TestCase):
    def setup_method(self, _):
        import transaction

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Functionality, Role
        from c2cgeoportal_commons.models.static import User

        create_default_ogcserver()
        role1 = Role(name="__test_role1")
        user1 = User(username="__test_user1", password="__test_user1", settings_role=role1, roles=[role1])
        role2 = Role(name="__test_role2")
        user2 = User(username="__test_user2", password="__test_user2", settings_role=role2, roles=[role2])
        role3 = Role(name="__test_role3")
        role4 = Role(name="__test_role4")
        user3 = User(
            username="__test_user3", password="__test_user3", roles=[role3, role4], settings_role=role3
        )

        functionality1 = Functionality("__test_s", "db")
        functionality2 = Functionality("__test_a", "db1")
        functionality3 = Functionality("__test_a", "db2")
        functionality4 = Functionality("__test_b", "db")
        role2.functionalities = [functionality1, functionality2, functionality3]
        role3.functionalities = [functionality1, functionality2]
        role4.functionalities = [functionality2, functionality3, functionality4]

        DBSession.add_all([user1, user2, user3, role1, role2])
        transaction.commit()

    def teardown_method(self, _):
        import transaction

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Functionality, OGCServer, Role
        from c2cgeoportal_commons.models.static import User

        transaction.commit()

        for user_name in ("__test_user1", "__test_user2", "__test_user3"):
            for o in DBSession.query(User).filter(User.username == user_name).all():
                o.functionalities = []
                DBSession.delete(o)
        for role_name in ("__test_role1", "__test_role2", "__test_role3", "__test_role4"):
            for o in DBSession.query(Role).filter(Role.name == role_name).all():
                o.functionalities = []
                DBSession.delete(o)
        for func_name in ("__test_s", "__test_a", "__test_b"):
            DBSession.query(Functionality).filter(Functionality.name == func_name).delete()
        DBSession.query(OGCServer).delete()

        transaction.commit()

    def test_functionalities(self):
        from tests.functional import create_dummy_request

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.lib.functionality import get_functionality

        request = create_dummy_request()
        request.user = None
        request1 = create_dummy_request()
        request1.user = DBSession.query(User).filter(User.username == "__test_user1").one()
        request2 = create_dummy_request()
        request2.user = DBSession.query(User).filter(User.username == "__test_user2").one()
        request3 = create_dummy_request()
        request3.user = DBSession.query(User).filter(User.username == "__test_user3").one()

        settings = {
            "admin_interface": {
                "available_functionalities": [
                    {"name": "__test_a"},
                    {"name": "__test_b", "single": True},
                    {"name": "__test_s", "single": True},
                ]
            }
        }
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
        request3.registry.settings.update(settings)
        self.assertEqual(get_functionality("__test_s", request, False), [])
        self.assertEqual(get_functionality("__test_a", request, False), [])
        self.assertEqual(get_functionality("__test_s", request1, False), [])
        self.assertEqual(get_functionality("__test_a", request1, False), [])
        self.assertEqual(get_functionality("__test_s", request2, False), ["db"])
        self.assertEqual(set(get_functionality("__test_a", request2, False)), {"db1", "db2"})
        self.assertEqual(get_functionality("__test_s", request3, False), ["db"])
        self.assertEqual(set(get_functionality("__test_a", request3, False)), {"db1", "db2"})
        self.assertEqual(get_functionality("__test_b", request3, False), [])

        fill_tech_user_functionality(
            "registered", (("__test_s", "registered"), ("__test_a", "r1"), ("__test_a", "r2"))
        )
        settings = {
            "admin_interface": {"available_functionalities": [{"name": "__test_a"}, {"name": "__test_s"}]}
        }
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
        request1.user = DBSession.query(User).filter(User.username == "__test_user1").one()
        request2.user = DBSession.query(User).filter(User.username == "__test_user2").one()
        request3.user = DBSession.query(User).filter(User.username == "__test_user3").one()
        self.assertEqual(get_functionality("__test_s", request, False), [])
        self.assertEqual(get_functionality("__test_a", request, False), [])
        self.assertEqual(get_functionality("__test_s", request1, False), ["registered"])
        self.assertEqual(set(get_functionality("__test_a", request1, False)), {"r1", "r2"})
        self.assertEqual(get_functionality("__test_s", request2, False), ["db"])
        self.assertEqual(set(get_functionality("__test_a", request2, False)), {"db1", "db2"})

        fill_tech_user_functionality("registered", [])
        fill_tech_user_functionality(
            "anonymous", (("__test_s", "anonymous"), ("__test_a", "a1"), ("__test_a", "a2"))
        )
        settings = {
            "admin_interface": {"available_functionalities": [{"name": "__test_a"}, {"name": "__test_s"}]}
        }
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
        request1.user = DBSession.query(User).filter(User.username == "__test_user1").one()
        request2.user = DBSession.query(User).filter(User.username == "__test_user2").one()
        request3.user = DBSession.query(User).filter(User.username == "__test_user3").one()
        self.assertEqual(get_functionality("__test_s", request, False), ["anonymous"])
        self.assertEqual(set(get_functionality("__test_a", request, False)), {"a1", "a2"})
        self.assertEqual(get_functionality("__test_s", request1, False), ["anonymous"])
        self.assertEqual(set(get_functionality("__test_a", request1, False)), {"a1", "a2"})
        self.assertEqual(get_functionality("__test_s", request2, False), ["db"])
        self.assertEqual(set(get_functionality("__test_a", request2, False)), {"db1", "db2"})

        fill_tech_user_functionality(
            "registered", (("__test_s", "registered"), ("__test_a", "r1"), ("__test_a", "r2"))
        )
        fill_tech_user_functionality(
            "anonymous", (("__test_s", "anonymous"), ("__test_a", "a1"), ("__test_a", "a2"))
        )
        settings = {
            "admin_interface": {"available_functionalities": [{"name": "__test_a"}, {"name": "__test_s"}]}
        }
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
        request1.user = DBSession.query(User).filter(User.username == "__test_user1").one()
        request2.user = DBSession.query(User).filter(User.username == "__test_user2").one()
        request3.user = DBSession.query(User).filter(User.username == "__test_user3").one()
        self.assertEqual(get_functionality("__test_s", request, False), ["anonymous"])
        self.assertEqual(set(get_functionality("__test_a", request, False)), {"a1", "a2"})
        self.assertEqual(get_functionality("__test_s", request1, False), ["registered"])
        self.assertEqual(set(get_functionality("__test_a", request1, False)), {"r1", "r2"})
        self.assertEqual(get_functionality("__test_s", request2, False), ["db"])
        self.assertEqual(set(get_functionality("__test_a", request2, False)), {"db1", "db2"})

    def test_web_client_functionalities(self):
        from tests.functional import create_dummy_request

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        request = create_dummy_request()
        request.static_url = lambda url: "http://example.com/dummy/static/url"
        request1 = create_dummy_request()
        request1.static_url = lambda url: "http://example.com/dummy/static/url"
        request1.user = DBSession.query(User).filter(User.username == "__test_user1").one()
        request2 = create_dummy_request()
        request2.static_url = lambda url: "http://example.com/dummy/static/url"
        request2.user = DBSession.query(User).filter(User.username == "__test_user2").one()

        fill_tech_user_functionality(
            "registered", (("__test_s", "registered"), ("__test_a", "r1"), ("__test_a", "r2"))
        )
        fill_tech_user_functionality(
            "anonymous", (("__test_s", "anonymous"), ("__test_a", "a1"), ("__test_a", "a2"))
        )
        settings = {
            "functionalities": {"available_in_templates": ["__test_s", "__test_a"]},
            "admin_interface": {"available_functionalities": [{"name": "__test_a"}, {"name": "__test_s"}]},
        }
        request.registry.settings.update(settings)
        request1.registry.settings.update(settings)
        request2.registry.settings.update(settings)
