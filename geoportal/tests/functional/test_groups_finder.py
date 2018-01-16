# -*- coding: utf-8 -*-

# Copyright (c) 2011-2018, Camptocamp SA
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


from unittest import TestCase

from tests.functional import (  # noqa
    teardown_common as teardown_module,
    setup_common as setup_module,
    create_dummy_request,
)


class TestGroupsFinder(TestCase):

    def setup_method(self, _):
        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User

        r = Role(name="__test_role")
        u = User(
            username="__test_user",
            password="__test_user",
            role=r
        )

        DBSession.add_all([r, u])
        transaction.commit()

    def teardown_method(self, _):
        import transaction
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role
        from c2cgeoportal_commons.models.static import User

        transaction.commit()

        DBSession.query(User).filter_by(username="__test_user").delete()
        DBSession.query(Role).filter_by(name="__test_role").delete()
        transaction.commit()

    def test_it(self):
        from c2cgeoportal_geoportal.resources import defaultgroupsfinder
        request = create_dummy_request(authentication=False, user="__test_user")
        roles = defaultgroupsfinder("__test_user", request)
        self.assertEqual(roles, ["__test_role"])
