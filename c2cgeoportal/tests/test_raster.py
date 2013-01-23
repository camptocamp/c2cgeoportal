# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 by Camptocamp SA


from unittest import TestCase


class TestRasterViews(TestCase):

    def test_raster(self):
        from decimal import Decimal
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.raster import Raster

        request = DummyRequest()
        request.registry.settings = {
            "raster": {
                "dem1": {"file": "c2cgeoportal/tests/data/dem.shp",
                         "round": 0.1},
                "dem2": {"file": "c2cgeoportal/tests/data/dem.shp",
                         "round": 1},
                "dem3": {"file": "c2cgeoportal/tests/data/dem.shp"}
            }
        }
        raster = Raster(request)

        request.params['lon'] = '565000'
        request.params['lat'] = '218000'
        result = raster.raster()
        self.assertEqual(result['dem1'], None)
        self.assertEqual(result['dem2'], None)
        self.assertEqual(result['dem3'], None)

        request.params['lon'] = '548000'
        request.params['lat'] = '216000'
        result = raster.raster()
        self.assertAlmostEqual(result['dem1'], Decimal('1168.9'))
        self.assertAlmostEqual(result['dem2'], Decimal('1169'))
        self.assertAlmostEqual(result['dem3'], Decimal('1168.85998535'))

        request.params['layers'] = 'dem2'
        result = raster.raster()
        self.assertFalse('dem1' in result)
        self.assertFalse('dem3' in result)
        self.assertAlmostEqual(result['dem2'], Decimal('1169'))

        # test wrong layer name
        request.params['layers'] = 'wrong'
        self.assertRaises(HTTPNotFound, raster.raster)

    def test_absolute_path(self):
        from c2cgeoportal.lib.raster.georaster import GeoRaster
        gr = GeoRaster("c2cgeoportal/tests/data/dem_absolute.shp")
        tile = gr._get_tile(548000, 216000)
        self.assertEqual(tile.filename,
                         '/home/sbrunner/regiogis/regiogis/c2cgeoportal/'
                         'c2cgeoportal/tests/data/dem.bt')

    def test_profile_json(self):
        from decimal import Decimal
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.profile import Profile

        request = DummyRequest()
        request.registry.settings = {
            "raster": {
                "dem": {"file": "c2cgeoportal/tests/data/dem.shp", "round": 4},
                "dem2": {"file": "c2cgeoportal/tests/data/dem.shp", "round": 4}
            }
        }
        profile = Profile(request)

        request.params['nbPoints'] = '3'
        request.params['geom'] = '{"type":"LineString",' \
                                  '"coordinates":[[548009.5,215990],' \
                                                 '[547990,216009.5]]}'
        result = profile.json()
        self.assertEqual(len(result['profile']), 3)
        self.assertAlmostEqual(result['profile'][0]['y'], 215990)
        self.assertAlmostEqual(result['profile'][0]['values']['dem2'], 1166)
        self.assertAlmostEqual(result['profile'][0]['values']['dem'], 1166)
        self.assertAlmostEqual(result['profile'][0]['dist'], Decimal('0.0'))
        self.assertAlmostEqual(result['profile'][0]['x'], 548009.5)
        self.assertAlmostEqual(result['profile'][1]['y'], 215996.5)
        self.assertAlmostEqual(result['profile'][1]['values']['dem2'], 1181)
        self.assertAlmostEqual(result['profile'][1]['values']['dem'], 1181)
        self.assertAlmostEqual(result['profile'][1]['dist'], Decimal('9.2'))
        self.assertAlmostEqual(result['profile'][1]['x'], 548003.0)
        self.assertAlmostEqual(result['profile'][2]['y'], 216003.0)
        self.assertAlmostEqual(result['profile'][2]['values']['dem'], 1181)
        self.assertAlmostEqual(result['profile'][2]['values']['dem2'], 1181)
        self.assertAlmostEqual(result['profile'][2]['dist'], Decimal('18.4'))
        self.assertAlmostEqual(result['profile'][2]['x'], 547996.5)

        request.params['layers'] = 'dem'
        result = profile.json()
        self.assertEqual(len(result['profile']), 3)
        self.assertAlmostEqual(result['profile'][0]['y'], 215990)
        self.assertAlmostEqual(result['profile'][0]['values']['dem'], 1166)
        self.assertAlmostEqual(result['profile'][0]['dist'], Decimal('0.0'))
        self.assertAlmostEqual(result['profile'][0]['x'], 548009.5)
        self.assertAlmostEqual(result['profile'][1]['y'], 215996.5)
        self.assertAlmostEqual(result['profile'][1]['values']['dem'], 1181)
        self.assertAlmostEqual(result['profile'][1]['dist'], Decimal('9.2'))
        self.assertAlmostEqual(result['profile'][1]['x'], 548003.0)
        self.assertAlmostEqual(result['profile'][2]['y'], 216003.0)
        self.assertAlmostEqual(result['profile'][2]['values']['dem'], 1181)
        self.assertAlmostEqual(result['profile'][2]['dist'], Decimal('18.4'))
        self.assertAlmostEqual(result['profile'][2]['x'], 547996.5)

        # test length = 0
        request.params['geom'] = '{"type":"LineString",' \
                                  '"coordinates":[[548000,216000]]}'
        result = profile.json()
        self.assertEqual(len(result['profile']), 1)
        self.assertAlmostEqual(result['profile'][0]['y'], 216000)
        self.assertAlmostEqual(result['profile'][0]['values']['dem'], 1169)
        self.assertAlmostEqual(result['profile'][0]['dist'], Decimal('0.0'))
        self.assertAlmostEqual(result['profile'][0]['x'], 548000)

        # test cur_nb_points < 1
        request.params['geom'] = '{"type":"LineString",' \
                                  '"coordinates":[[548000,216000],' \
                                                 '[548001,216001],' \
                                                 '[548009,216009]]}'
        result = profile.json()
        self.assertEqual(len(result['profile']), 3)
        self.assertAlmostEqual(result['profile'][0]['y'], 216000)
        self.assertAlmostEqual(result['profile'][0]['values']['dem'], 1169)
        self.assertAlmostEqual(result['profile'][0]['dist'], Decimal('0.0'))
        self.assertAlmostEqual(result['profile'][0]['x'], 548000)
        self.assertAlmostEqual(result['profile'][1]['y'], 216003.66666666666)
        self.assertAlmostEqual(result['profile'][1]['values']['dem'], 1155)
        self.assertAlmostEqual(result['profile'][1]['dist'], Decimal('5.2'))
        self.assertEqual(result['profile'][1]['x'], 548003.66666666663)
        self.assertAlmostEqual(result['profile'][2]['y'], 216006.33333333334)
        self.assertAlmostEqual(result['profile'][2]['values']['dem'], 1154)
        self.assertAlmostEqual(result['profile'][2]['dist'], Decimal('9.0'))
        self.assertAlmostEqual(result['profile'][2]['x'], 548006.33333333337)

        # test wrong layer name
        request.params['layers'] = 'wrong'
        self.assertRaises(HTTPNotFound, profile.json)

    def test_profile_csv(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal.views.profile import Profile

        request = DummyRequest()
        request.registry.settings = {
            "raster": {
                "dem": {"file": "c2cgeoportal/tests/data/dem.shp", "round": 1},
                "dem2": {"file": "c2cgeoportal/tests/data/dem.shp", "round": 1}
            }
        }
        profile = Profile(request)

        request.params['nbPoints'] = '3'
        request.params['geom'] = '{"type":"LineString",' \
                                  '"coordinates":[[548009.5,215990],' \
                                                 '[547990,216009.5]]}'
        response = profile.csv()
        self.assertEqual(response.body, """distance,dem2,dem,x,y
0.0,1166,1166,548009,215990
9.2,1181,1181,548003,215996
18.4,1181,1181,547996,216003""")

        request.params['layers'] = 'dem'
        response = profile.csv()
        self.assertEqual(response.body, """distance,dem,x,y
0.0,1166,548009,215990
9.2,1181,548003,215996
18.4,1181,547996,216003""")
