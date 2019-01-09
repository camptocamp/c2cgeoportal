# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019, Camptocamp SA
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


import pyramid.registry
from unittest import TestCase
from pyramid.testing import DummyRequest
from c2cgeoportal_geoportal.lib.caching import init_region


def handler(request):
    return request.response


class MyRequest(DummyRequest):
    def __init__(self, path_info):
        self.path_info = path_info


class TestCacheBuster(TestCase):

    @classmethod
    def setup_class(cls):
        init_region({"backend": "dogpile.cache.memory"})

    def test_replace(self):
        from c2cgeoportal_geoportal.lib.cacheversion import CachebusterTween

        registry = pyramid.registry.Registry()
        registry.settings = {'cache_path': ['test']}
        ctf = CachebusterTween(handler, registry)
        request = MyRequest("/test/123456/build.css")
        ctf(request)
        self.assertEqual(request.path_info, "/test/build.css")

    def test_noreplace(self):
        from c2cgeoportal_geoportal.lib.cacheversion import CachebusterTween

        registry = pyramid.registry.Registry()
        registry.settings = {'cache_path': ['test']}
        ctf = CachebusterTween(handler, registry)
        request = MyRequest("/test2/123456/build.css")
        ctf(request)
        self.assertEqual(request.path_info, "/test2/123456/build.css")
