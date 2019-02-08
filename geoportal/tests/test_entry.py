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
from pyramid import testing
from c2c.template.config import config


def setup_module():  # noqa
    from c2cgeoportal_geoportal import caching
    config._config = {
        'schema': 'main',
        'schema_static': 'main_static',
        'srid': 21781,
    }
    caching.init_region({
        "backend": "dogpile.cache.null",
    })


class TestEntryView(TestCase):

    def setup_method(self, _):
        testing.setUp(
            settings={
                "default_locale_name": "fr",
                "default_max_age": 1000,
            }
        )

    def teardown_method(self, _):
        testing.tearDown()

    def test_decimal_json(self):
        from decimal import Decimal
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal import DecimalJSON
        renderer = DecimalJSON()(None)
        request = DummyRequest()
        request.user = None
        system = {"request": request}

        self.assertEqual(
            renderer({"a": Decimal("3.3")}, system),
            '{"a": 3.3}'
        )
        self.assertEqual(request.response.content_type, "application/json")

    def test__get_child_layers_info_with_scalehint(self):
        import math
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = DummyRequest()
        request.user = None
        entry = Entry(request)

        class Layer:
            pass

        child_layer_1 = Layer()
        child_layer_1.name = "layer_1"
        child_layer_1.scaleHint = {
            "min": 1 * math.sqrt(2),
            "max": 2 * math.sqrt(2)
        }
        child_layer_1.layers = []

        child_layer_2 = Layer()
        child_layer_2.name = "layer_2"
        child_layer_2.scaleHint = {
            "min": 3 * math.sqrt(2),
            "max": 4 * math.sqrt(2)
        }
        child_layer_2.layers = []

        layer = Layer()
        layer.layers = [child_layer_1, child_layer_2]

        child_layers_info = entry._get_child_layers_info_1(layer)

        expected = [{
            "name": "layer_1",
            "minResolutionHint": 1.0,
            "maxResolutionHint": 2.0
        }, {
            "name": "layer_2",
            "minResolutionHint": 3.0,
            "maxResolutionHint": 4.0
        }]
        self.assertEqual(child_layers_info, expected)

    def test_login(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = DummyRequest()
        request.is_valid_referer = True
        request.user = None
        entry = Entry(request)

        request.path = "/for_test"
        expected = {
            "lang": "fr",
            "came_from": "/for_test",
        }
        self.assertEqual(entry.loginform403(), expected)

        request.params = {
            "came_from": "/for_a_second_test",
        }
        entry = Entry(request)
        expected = {
            "lang": "fr",
            "came_from": "/for_a_second_test",
        }
        self.assertEqual(entry.loginform(), expected)

        entry = Entry(request)
        request.params = {}
        expected = {
            "lang": "fr",
            "came_from": "/",
        }
        self.assertEqual(entry.loginform(), expected)

        request.registry.settings = {
            "functionalities": {
                "anonymous": {
                    "func": ["anon"],
                    "toto": "titi"
                },
                "registered": {
                    "func": ["reg"]
                },
                "available_in_templates": ["func"]
            },
            "admin_interface": {
                "available_functionalities": [{"name": "func"}]
            }
        }
        entry = Entry(request)
        expected = {
            "functionalities": {
                "func": ["anon"]
            }
        }
        self.assertEqual(entry.loginuser(), expected)

        class G:
            id = 123

            def __init__(self, name, functionalities):
                self.name = name
                self.functionalities = functionalities

        class U:
            username = "__test_user"
            is_password_changed = True
            email = "info@example.com"

            def __init__(self, role="__test_role", functionalities=None):
                if functionalities is None:
                    functionalities = []
                self.roles = [G(role, functionalities)]

        request.user = U()
        entry = Entry(request)
        expected = {
            "success": True,
            "username": "__test_user",
            "email": "info@example.com",
            "is_password_changed": True,
            "roles": [{
                "name": "__test_role",
                "id": 123,
            }],
            "functionalities": {
                "func": ["reg"]
            }
        }
        self.assertEqual(entry.loginuser(), expected)

        class F:
            name = "func"
            value = "user"

        request.user = U("__test_role2", [F()])
        entry = Entry(request)
        expected = {
            "success": True,
            "username": "__test_user",
            'email': 'info@example.com',
            "is_password_changed": True,
            "roles": [{
                "name": "__test_role2",
                "id": 123,
            }],
            "functionalities": {
                "func": ["user"]
            }
        }
        self.assertEqual(entry.loginuser(), expected)

    def test__get_child_layers_info_without_scalehint(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = DummyRequest()
        request.user = None
        entry = Entry(request)

        class Layer:
            pass

        child_layer_1 = Layer()
        child_layer_1.name = "layer_1"
        child_layer_1.scaleHint = None
        child_layer_1.layers = []

        child_layer_2 = Layer()
        child_layer_2.name = "layer_2"
        child_layer_2.scaleHint = None
        child_layer_2.layers = []

        layer = Layer()
        layer.layers = [child_layer_1, child_layer_2]

        child_layers_info = entry._get_child_layers_info_1(layer)

        expected = [{
            "name": "layer_1",
            "minResolutionHint": 0.0,
            "maxResolutionHint": 999999999.0,
        }, {
            "name": "layer_2",
            "minResolutionHint": 0.0,
            "maxResolutionHint": 999999999.0,
        }]
        self.assertEqual(child_layers_info, expected)
