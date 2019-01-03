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


class TestFunctionalities(TestCase):
    def test_get_config_functionality(self):
        from c2cgeoportal_geoportal.lib import get_types_map
        from c2cgeoportal_geoportal.lib import functionality

        types = get_types_map(["func"])

        class Registry:
            settings = {}

        class Request:
            registry = Registry()

        request = Request()
        request.registry.settings = {
            "functionalities": {
                "registered": {
                    "func": 10
                },
                "anonymous": {
                    "func": 20
                }
            }
        }
        functionality.FUNCTIONALITIES_TYPES = None
        errors = set()

        f = functionality._get_config_functionality("func", True, types, request, errors)
        self.assertEqual(errors, set())
        self.assertEqual(f, [10])

        f = functionality._get_config_functionality("func", False, types, request, errors)
        self.assertEqual(errors, set())
        self.assertEqual(f, [20])

        request.registry.settings = {
            "functionalities": {
                "registered": {
                    "not_func": 10
                },
                "anonymous": {
                    "func": 20
                }
            }
        }
        functionality.FUNCTIONALITIES_TYPES = None
        f = functionality._get_config_functionality("func", True, types, request, errors)
        self.assertEqual(errors, set())
        self.assertEqual(f, [20])

        request.registry.settings = {
            "functionalities": {
                "registered": {
                    "func": 10
                },
                "anonymous": {
                    "not_func": 20
                }
            }
        }
        functionality.FUNCTIONALITIES_TYPES = None
        f = functionality._get_config_functionality("func", False, types, request, errors)
        self.assertEqual(errors, set())
        self.assertEqual(f, [])
