# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
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


def setUpModule():
    import c2cgeoportal
    c2cgeoportal.schema = 'main'
    c2cgeoportal.srid = 21781
    c2cgeoportal.caching.init_region({'backend': 'dogpile.cache.memory'})


class TestEntryView(TestCase):

    def setUp(self):
        from pyramid import testing
        self.config = testing.setUp(settings={})

    def test_decimal_JSON(self):
        from decimal import Decimal
        from pyramid.testing import DummyRequest
        from c2cgeoportal import DecimalJSON
        renderer = DecimalJSON()(None)
        request = DummyRequest()
        system = {'request': request}

        self.assertEquals(renderer({'a': Decimal('3.3')}, system),
                '{"a": 3.3}')
        self.assertEquals(request.response.content_type, 'application/json')

        request.params = {'callback': 'abc'}
        self.assertEquals(renderer({'a': Decimal('3.3')}, system),
                'abc({"a": 3.3});')
        self.assertEquals(request.response.content_type, 'text/javascript')

        renderer = DecimalJSON(jsonp_param_name='cb')(None)
        request.params = {'cb': 'def'}
        self.assertEquals(renderer({'a': Decimal('3.3')}, system),
                'def({"a": 3.3});')
        self.assertEquals(request.response.content_type, 'text/javascript')

    def test__get_child_layers_info_with_scalehint(self):
        import math
        from pyramid.testing import DummyRequest
        from c2cgeoportal.views.entry import Entry

        request = DummyRequest()
        entry = Entry(request)

        class Layer(object):
            pass

        child_layer_1 = Layer()
        child_layer_1.name = 'layer_1'
        child_layer_1.scaleHint = {
                'min': 1 * math.sqrt(2),
                'max': 2 * math.sqrt(2)
                }
        child_layer_1.layers = []

        child_layer_2 = Layer()
        child_layer_2.name = 'layer_2'
        child_layer_2.scaleHint = {
                'min': 3 * math.sqrt(2),
                'max': 4 * math.sqrt(2)
                }
        child_layer_2.layers = []

        layer = Layer()
        layer.layers = [child_layer_1, child_layer_2]

        child_layers_info = entry._get_child_layers_info(layer)

        expected = [{
            'name': 'layer_1',
            'minResolutionHint': 1.0,
            'maxResolutionHint': 2.0
        }, {
            'name': 'layer_2',
            'minResolutionHint': 3.0,
            'maxResolutionHint': 4.0
        }]
        self.assertEqual(child_layers_info, expected)

    def test_login(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal.views.entry import Entry

        request = DummyRequest()
        request.params = { 'lang': 'en' }
        entry = Entry(request)

        request.path = '/for_test'
        expected = {
            'lang': 'en',
            'came_from': '/for_test',
        }
        self.assertEqual(entry.loginform403(), expected)

        request.params = {
            'came_from': '/for_a_second_test',
        }
        entry = Entry(request)
        expected = {
            'lang': 'en',
            'came_from': '/for_a_second_test',
        }
        self.assertEqual(entry.loginform(), expected)

        entry = Entry(request)
        request.params = {}
        expected = {
            'lang': 'en',
            'came_from': '/',
        }
        self.assertEqual(entry.loginform(), expected)


    def test__get_child_layers_info_without_scalehint(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal.views.entry import Entry

        request = DummyRequest()
        entry = Entry(request)

        class Layer(object):
            pass

        child_layer_1 = Layer()
        child_layer_1.name = 'layer_1'
        child_layer_1.scaleHint = None
        child_layer_1.layers = []

        child_layer_2 = Layer()
        child_layer_2.name = 'layer_2'
        child_layer_2.scaleHint = None
        child_layer_2.layers = []

        layer = Layer()
        layer.layers = [child_layer_1, child_layer_2]

        child_layers_info = entry._get_child_layers_info(layer)

        expected = [{
            'name': 'layer_1'
            }, {
            'name': 'layer_2',
            }]
        self.assertEqual(child_layers_info, expected)
