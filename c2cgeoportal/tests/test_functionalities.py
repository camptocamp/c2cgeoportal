# -*- coding: utf-8 -*-

from unittest import TestCase
from pyramid import testing

class TestFunctionalities(TestCase):
    def test_get_config_functionalities(self):
        from c2cgeoportal.lib.functionality import _get_config_functionalities

        f = _get_config_functionalities('func', True, {
            'registered_functionalities': {
                'func': 10
            },
            'anonymous_functionalities': {
                'func': 20
            }
        })
        self.assertEquals(f, 10)

        f = _get_config_functionalities('func', False, {
            'registered_functionalities': {
                'func': 10
            },
            'anonymous_functionalities': {
                'func': 20
            }
        })
        self.assertEquals(f, 20)

        f = _get_config_functionalities('func', True, {
            'registered_functionalities': {
                'not_func': 10
            },
            'anonymous_functionalities': {
                'func': 20
            }
        })
        self.assertEquals(f, 20)

        f = _get_config_functionalities('func', False, {
            'registered_functionalities': {
                'func': 10
            },
            'anonymous_functionalities': {
                'not_func': 20
            }
        })
        self.assertEquals(f, None)


