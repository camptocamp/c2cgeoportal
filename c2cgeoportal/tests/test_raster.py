# -*- coding: utf-8 -*-
from unittest import TestCase

class TestRasterViews(TestCase):
    def test_raster(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.raster import Raster

        request = DummyRequest()
        request.registry.settings = dict(raster=\
            '/var/www/vhosts/project/private/project/{\n' \
            + '"dem1": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp", "round": 0.1 },\n' \
            + '"dem2": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp", "round": 1 },\n' \
            + '"dem3": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp" }\n}')
        raster = Raster(request)

        request.params['lon'] = '565000'
        request.params['lat'] = '218000'
        assert raster.raster().body == '{"dem2": null, "dem3": null, "dem1": null}'

        request.params['lon'] = '548000'
        request.params['lat'] = '216000'
        assert raster.raster().body == '{"dem2": 1169, "dem3": 1168.85998535, "dem1": 1168.9}'

        request.params['layers'] = 'dem2'
        assert raster.raster().body == '{"dem2": 1169}'

        # test wrong layer name
        request.params['layers'] = 'wrong'
        try:
            raster.raster()
            assert False  # should launch en HTTPNotFound exception
        except HTTPNotFound:
            pass

    def test_absolute_path(self):
        from c2cgeoportal.lib.raster.georaster import GeoRaster
        gr = GeoRaster("c2cgeoportal/tests/data/dem_absolute.shp")
        tile = gr._get_tile(548000, 216000)
        assert tile.filename == '/home/sbrunner/regiogis/regiogis/c2cgeoportal/c2cgeoportal/tests/data/dem.bt'

    def test_profile_json(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.profile import Profile

        request = DummyRequest()
        request.registry.settings = dict(raster=\
            '/var/www/vhosts/project/private/project/{\n' \
            + '"dem": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp", "round": 1 },\n' \
            + '"dem2": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp", "round": 1 }\n}')
        profile = Profile(request)

        request.params['nbPoints'] = '3'
        request.params['geom'] = '{"type":"LineString","coordinates":[[548009.5,215990],[547990,216009.5]]}'
        assert profile.json().body == '{"profile": [' \
            + '{"y": 215990, "values": {"dem2": 1166, "dem": 1166}, "dist": 0.0, "x": 548009.5}, ' \
            + '{"y": 215996.5, "values": {"dem2": 1181, "dem": 1181}, "dist": 9.2, "x": 548003.0}, ' \
            + '{"y": 216003.0, "values": {"dem2": 1181, "dem": 1181}, "dist": 18.4, "x": 547996.5}]}'

        request.params['layers'] = 'dem'
        assert profile.json().body == '{"profile": [' \
            + '{"y": 215990, "values": {"dem": 1166}, "dist": 0.0, "x": 548009.5}, ' \
            + '{"y": 215996.5, "values": {"dem": 1181}, "dist": 9.2, "x": 548003.0}, ' \
            + '{"y": 216003.0, "values": {"dem": 1181}, "dist": 18.4, "x": 547996.5}]}'

        # test length = 0
        request.params['geom'] = '{"type":"LineString","coordinates":[[548000,216000]]}'
        assert profile.json().body == '{"profile": ' \
            + '[{"y": 216000, "values": {"dem": 1169}, "dist": 0.0, "x": 548000}]}'

        # test cur_nb_points < 1
        request.params['geom'] = '{"type":"LineString","coordinates":[[548000,216000],[548001,216001],[548009,216009]]}'
        assert profile.json().body == '{"profile": [' \
            + '{"y": 216000, "values": {"dem": 1169}, "dist": 0.0, "x": 548000}, ' \
            + '{"y": 216003.66666666666, "values": {"dem": 1155}, "dist": 5.2, "x": 548003.66666666663}, ' \
            + '{"y": 216006.33333333334, "values": {"dem": 1154}, "dist": 9.0, "x": 548006.33333333337}]}'

        # test wrong layer name
        request.params['layers'] = 'wrong'
        self.assertRaises(HTTPNotFound, profile.json)

    def test_profile_csv(self):
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal.views.profile import Profile

        request = DummyRequest()
        request.registry.settings = dict(raster=\
            '/var/www/vhosts/project/private/project/{\n' \
            + '"dem": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp", "round": 1 },\n' \
            + '"dem2": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp", "round": 1 }\n}')
        profile = Profile(request)

        request.params['nbPoints'] = '3'
        request.params['geom'] = '{"type":"LineString","coordinates":[[548009.5,215990],[547990,216009.5]]}'
        response = profile.csv()
        self.assertEquals(response.body, """distance,dem2,dem,x,y
0.0,1166,1166,548009,215990
9.2,1181,1181,548003,215996
18.4,1181,1181,547996,216003""")

        request.params['layers'] = 'dem'
        response = profile.csv()
        self.assertEquals(response.body, """distance,dem,x,y
0.0,1166,548009,215990
9.2,1181,548003,215996
18.4,1181,547996,216003""")
