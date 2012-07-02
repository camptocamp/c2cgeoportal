# -*- coding: utf-8 -*-
from unittest import TestCase


def setUpModule():
    import c2cgeoportal
    c2cgeoportal.schema = 'main'
    c2cgeoportal.srid = 21781


class TestEntryView(TestCase):

    def setUp(self):
        from pyramid import testing
        self.config = testing.setUp(
            settings={}   
            )

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
