# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


from unittest import TestCase


class TestFunctionalities(TestCase):
    def test_get_config_functionality(self):
        from c2cgeoportal.lib.functionality import _get_config_functionality

        f = _get_config_functionality('func', True, {
            'functionalities': {
                'registered': {
                    'func': 10
                },
                'anonymous': {
                    'func': 20
                }
            }
        })
        self.assertEquals(f, [10])

        f = _get_config_functionality('func', False, {
            'functionalities': {
                'registered': {
                    'func': 10
                },
                'anonymous': {
                    'func': 20
                }
            }
        })
        self.assertEquals(f, [20])

        f = _get_config_functionality('func', True, {
            'functionalities': {
                'registered': {
                    'not_func': 10
                },
                'anonymous': {
                    'func': 20
                }
            }
        })
        self.assertEquals(f, [20])

        f = _get_config_functionality('func', False, {
            'functionalities': {
                'registered': {
                    'func': 10
                },
                'anonymous': {
                    'not_func': 20
                }
            }
        })
        self.assertEquals(f, [])
