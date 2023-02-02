# Copyright (c) 2013-2023, Camptocamp SA
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

from pyramid.request import Request
from pyramid.threadlocal import get_current_registry

from c2cgeoportal_geoportal import MapserverproxyRoutePredicate


class TestMapserverproxyRoutePredicate(TestCase):
    predicate = MapserverproxyRoutePredicate(None, None)

    def test_hide_capabilities_unset(self):
        request = Request.blank("/test")
        request.registry = get_current_registry()
        request.registry.settings = {}
        self.assertTrue(self.predicate(None, request))

    def test_hide_capabilities_set_no_request_param(self):
        request = Request.blank("/test")
        request.registry = get_current_registry()
        request.registry.settings = {"hide_capabilities": True}
        self.assertTrue(self.predicate(None, request))

    def test_hide_capabilities_set_not_get_capabilities_request(self):
        request = Request.blank("/test?REQUEST=GetMap")
        request.registry = get_current_registry()
        request.registry.settings = {"hide_capabilities": True}
        self.assertTrue(self.predicate(None, request))

    def test_hide_capabilities_set_get_capabilities_request(self):
        request = Request.blank("/test?REQUEST=GetCapabilities")
        request.registry = get_current_registry()
        request.registry.settings = {"hide_capabilities": True}
        self.assertFalse(self.predicate(None, request))
