# Copyright (c) 2022-2022, Camptocamp SA
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

# pylint: disable=missing-docstring


from unittest import TestCase

import transaction
from tests.functional import cleanup_db, create_dummy_request
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import setup_db
from tests.functional import teardown_common as teardown_module  # noqa


class TestOGCProxy(TestCase):
    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import OGCServer

        setup_db()

        ogcserver = OGCServer(name="MixedCaseOGCServer")
        ogcserver.url = "http://mapserver:8080/"
        DBSession.add(ogcserver)
        DBSession.flush()

        transaction.commit()

    def teardown_method(self, _):
        cleanup_db()

    def test_ogcserver(self):
        from c2cgeoportal_commons.models.main import OGCServer
        from c2cgeoportal_geoportal.views.ogcproxy import OGCProxy

        request = create_dummy_request()
        request.params.update({"ogcserver": "MixedCaseOGCServer"})
        proxy = OGCProxy(request)
        assert isinstance(proxy.ogc_server, OGCServer)
        assert proxy.ogc_server.name == "MixedCaseOGCServer"

        request = create_dummy_request()
        request.params.update({"OGCSERVER": "MixedCaseOGCServer"})
        proxy = OGCProxy(request)
        assert isinstance(proxy.ogc_server, OGCServer)
        assert proxy.ogc_server.name == "MixedCaseOGCServer"
