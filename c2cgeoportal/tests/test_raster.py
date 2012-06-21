# -*- coding: utf-8 -*-

def test_raster():
    from pyramid.testing import DummyRequest
    from c2cgeoportal.views.raster import Raster
    import simplejson as json

    request = DummyRequest()
    request.registry.settings = dict(raster=\
        '/home/sbrunner/regiogis/regiogis/{\n' \
        + '"dem1": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp", "round": 0.1 },\n' \
        + '"dem2": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp", "round": 1 },\n' \
        + '"dem3": { "type": "shp_index", "file": "c2cgeoportal/tests/data/dem.shp" }\n}')
    raster = Raster(request)

    request.params['lon'] = 565000
    request.params['lat'] = 218000
    assert json.dumps(raster.raster()) == '{"dem2": null, "dem3": null, "dem1": null}'

    request.params['lon'] = 548000
    request.params['lat'] = 216000
    print json.dumps(raster.raster())
    assert json.dumps(raster.raster()) == '{"dem2": "1169", "dem3": "1168.85998535", "dem1": "1168.9"}'

    from c2cgeoportal.lib.raster.georaster import GeoRaster
    gr = GeoRaster("c2cgeoportal/tests/data/dem_absolute.shp")
    tile = gr._get_tile(548000, 216000)
    print tile.filename
    assert tile.filename == '/home/sbrunner/regiogis/regiogis/c2cgeoportal/c2cgeoportal/tests/data/dem.bt'
