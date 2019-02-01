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

from unittest import TestCase

from pyramid.request import Request

from c2cgeoportal_geoportal import OgcproxyRoutePredicate


class TestMapserverproxyRoutePredicate(TestCase):

    predicate = OgcproxyRoutePredicate(None, None)

    def test_no_url(self):
        request = Request.blank("/test")
        self.assertFalse(self.predicate(None, request))

    def test_invalid(self):
        request = Request.blank("/test?url=http://askdljfhaskdjhfakldjs.com/")
        self.assertFalse(self.predicate(None, request))

    def test_google(self):
        request = Request.blank("/test?url=http://google.com/")
        self.assertTrue(self.predicate(None, request))

    def test_1234(self):
        request = Request.blank("/test?url=http://1.2.3.4/")
        self.assertTrue(self.predicate(None, request))

    def test_local(self):
        request = Request.blank("/test?url=http://127.2.3.4/")
        self.assertFalse(self.predicate(None, request))

    def test_10(self):
        request = Request.blank("/test?url=http://10.2.3.4/")
        self.assertFalse(self.predicate(None, request))

    def test_192_168(self):
        request = Request.blank("/test?url=http://192.168.3.4/")
        self.assertFalse(self.predicate(None, request))

    def test_172_16_0_0(self):
        request = Request.blank("/test?url=http://172.16.0.0/")
        self.assertFalse(self.predicate(None, request))

    def test_172_31_255_255(self):
        request = Request.blank("/test?url=http://172.31.255.255/")
        self.assertFalse(self.predicate(None, request))

    def test_172_15_255_255(self):
        request = Request.blank("/test?url=http://172.15.255.255/")
        self.assertTrue(self.predicate(None, request))

    def test_172_32_0_0(self):
        request = Request.blank("/test?url=http://172.32.0.0/")
        self.assertTrue(self.predicate(None, request))
