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


class TestRasterViews(TestCase):

    def test_raster(self):
        from decimal import Decimal
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal_geoportal.views.raster import Raster

        request = DummyRequest()
        request.registry.settings = {
            "raster": {
                "dem1": {
                    "file": "/src/geoportal/tests/data/dem.shp",
                    "round": 0.1
                },
                "dem2": {
                    "file": "/src/geoportal/tests/data/dem.shp",
                    "round": 1
                },
                "dem3": {"file": "/src/geoportal/tests/data/dem.shp"}
            }
        }
        raster = Raster(request)

        request.params["lon"] = "565000"
        request.params["lat"] = "218000"
        result = raster.raster()
        self.assertEqual(result["dem1"], None)
        self.assertEqual(result["dem2"], None)
        self.assertEqual(result["dem3"], None)

        request.params["lon"] = "548000"
        request.params["lat"] = "216000"
        result = raster.raster()
        self.assertAlmostEqual(result["dem1"], Decimal("1171.6"))
        self.assertAlmostEqual(result["dem2"], Decimal("1172"))
        self.assertAlmostEqual(result["dem3"], Decimal("1171.62"))

        request.params["layers"] = "dem2"
        result = raster.raster()
        self.assertFalse("dem1" in result)
        self.assertFalse("dem3" in result)
        self.assertAlmostEqual(result["dem2"], Decimal("1172"))

        # test wrong layer name
        request.params["layers"] = "wrong"
        self.assertRaises(HTTPNotFound, raster.raster)

    def test_raster_angle(self):
        from decimal import Decimal
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.raster import Raster

        request = DummyRequest()
        request.registry.settings = {
            "raster": {
                "dem5": {
                    "file": "/src/geoportal/tests/data/dem4.bt",
                    "type": "gdal",
                    "round": 0.01
                }
            }
        }
        raster = Raster(request)

        # Upper left
        request.params["lon"] = "547990.0"
        request.params["lat"] = "216009.1"
        result = raster.raster()
        self.assertEqual(result["dem5"], Decimal("1164.2"))
        request.params["lon"] = "547990.9"
        request.params["lat"] = "216010.0"
        result = raster.raster()
        self.assertEqual(result["dem5"], Decimal("1164.2"))

        # Lower right
        request.params["lon"] = "547996.0"
        request.params["lat"] = "216003.1"
        result = raster.raster()
        self.assertEqual(result["dem5"], Decimal("1180.77"))
        request.params["lon"] = "547996.9"
        request.params["lat"] = "216004.0"
        result = raster.raster()
        self.assertEqual(result["dem5"], Decimal("1180.77"))

        # Out
        request.params["lon"] = "547997.4"
        request.params["lat"] = "216003.5"
        result = raster.raster()
        self.assertEqual(result["dem5"], None)

    def test_raster_vrt(self):
        from decimal import Decimal
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.raster import Raster

        request = DummyRequest()
        request.registry.settings = {
            "raster": {
                "dem6": {
                    "file": "/src/geoportal/tests/data/dem4.vrt",
                    "type": "gdal",
                    "round": 0.01
                }
            }
        }
        raster = Raster(request)

        # Upper left
        request.params["lon"] = "547990.4"
        request.params["lat"] = "216009.5"
        result = raster.raster()
        self.assertEqual(result["dem6"], Decimal("1164.2"))

    def test_absolute_path(self):
        import fiona
        with fiona.open("/src/geoportal/tests/data/dem_absolute.shp") as collection:
            tiles = [e for e in collection.filter(mask={
                "type": "Point",
                "coordinates": [548000, 216000],
            })]

        self.assertEqual(
            tiles[0]["properties"]["location"],
            "/home/sbrunner/regiogis/regiogis/c2cgeoportal/c2cgeoportal/tests/data/dem.bt")

    def test_profile_json(self):
        from decimal import Decimal
        from pyramid.testing import DummyRequest
        from pyramid.httpexceptions import HTTPNotFound
        from c2cgeoportal_geoportal.views.profile import Profile

        request = DummyRequest()
        request.registry.settings = {
            "raster": {
                "dem": {"file": "/src/geoportal/tests/data/dem.shp", "round": 4},
                "dem2": {"file": "/src/geoportal/tests/data/dem.shp", "round": 4}
            }
        }
        profile = Profile(request)

        request.params["nbPoints"] = "3"
        request.params["geom"] = '{"type":"LineString",' \
            '"coordinates":[[548009.5,215990],[547990,216009.5]]}'
        result = profile.json()
        self.assertEqual(len(result["profile"]), 4)
        self.assertAlmostEqual(result["profile"][0]["y"], 215990)
        self.assertAlmostEqual(result["profile"][0]["values"]["dem2"], None)
        self.assertAlmostEqual(result["profile"][0]["values"]["dem"], None)
        self.assertAlmostEqual(result["profile"][0]["dist"], Decimal("0.0"))
        self.assertAlmostEqual(result["profile"][0]["x"], 548009.5)
        self.assertAlmostEqual(result["profile"][1]["y"], 215996.5)
        self.assertAlmostEqual(result["profile"][1]["values"]["dem2"], 1181)
        self.assertAlmostEqual(result["profile"][1]["values"]["dem"], 1181)
        self.assertAlmostEqual(result["profile"][1]["dist"], Decimal("9.2"))
        self.assertAlmostEqual(result["profile"][1]["x"], 548003.0)
        self.assertAlmostEqual(result["profile"][2]["y"], 216003.0)
        self.assertAlmostEqual(result["profile"][2]["values"]["dem"], 1180)
        self.assertAlmostEqual(result["profile"][2]["values"]["dem2"], 1180)
        self.assertAlmostEqual(result["profile"][2]["dist"], Decimal("18.4"))
        self.assertAlmostEqual(result["profile"][2]["x"], 547996.5)
        self.assertAlmostEqual(result["profile"][3]["y"], 216009.5)
        self.assertAlmostEqual(result["profile"][3]["values"]["dem"], 1164)
        self.assertAlmostEqual(result["profile"][3]["values"]["dem2"], 1164)
        self.assertAlmostEqual(result["profile"][3]["dist"], Decimal("27.6"))
        self.assertAlmostEqual(result["profile"][3]["x"], 547990.0)

        request.params["layers"] = "dem"
        result = profile.json()
        self.assertEqual(len(result["profile"]), 4)
        self.assertAlmostEqual(result["profile"][0]["y"], 215990)
        self.assertAlmostEqual(result["profile"][0]["values"]["dem"], None)
        self.assertAlmostEqual(result["profile"][0]["dist"], Decimal("0.0"))
        self.assertAlmostEqual(result["profile"][0]["x"], 548009.5)
        self.assertAlmostEqual(result["profile"][1]["y"], 215996.5)
        self.assertAlmostEqual(result["profile"][1]["values"]["dem"], 1181)
        self.assertAlmostEqual(result["profile"][1]["dist"], Decimal("9.2"))
        self.assertAlmostEqual(result["profile"][1]["x"], 548003.0)
        self.assertAlmostEqual(result["profile"][2]["y"], 216003.0)
        self.assertAlmostEqual(result["profile"][2]["values"]["dem"], 1180)
        self.assertAlmostEqual(result["profile"][2]["dist"], Decimal("18.4"))
        self.assertAlmostEqual(result["profile"][2]["x"], 547996.5)
        self.assertAlmostEqual(result["profile"][3]["y"], 216009.5)
        self.assertAlmostEqual(result["profile"][3]["values"]["dem"], 1164)
        self.assertAlmostEqual(result["profile"][3]["dist"], Decimal("27.6"))
        self.assertAlmostEqual(result["profile"][3]["x"], 547990.0)

        # test length = 0
        request.params["geom"] = '{"type":"LineString",' \
            '"coordinates":[[548000,216000]]}'
        result = profile.json()
        self.assertEqual(len(result["profile"]), 1)
        self.assertAlmostEqual(result["profile"][0]["y"], 216000)
        self.assertAlmostEqual(result["profile"][0]["values"]["dem"], 1172)
        self.assertAlmostEqual(result["profile"][0]["dist"], Decimal("0.0"))
        self.assertAlmostEqual(result["profile"][0]["x"], 548000)

        # test cur_nb_points < 1
        request.params["geom"] = '{"type":"LineString",' \
            '"coordinates":[[548000,216000],[548001,216001],[548009,216009]]}'
        result = profile.json()
        self.assertEqual(len(result["profile"]), 5)
        self.assertAlmostEqual(result["profile"][0]["y"], 216000)
        self.assertAlmostEqual(result["profile"][0]["values"]["dem"], 1172)
        self.assertAlmostEqual(result["profile"][0]["dist"], Decimal("0.0"))
        self.assertAlmostEqual(result["profile"][0]["x"], 548000)
        self.assertAlmostEqual(result["profile"][1]["y"], 216001.0)
        self.assertAlmostEqual(result["profile"][1]["values"]["dem"], 1167)
        self.assertAlmostEqual(result["profile"][1]["dist"], Decimal("1.4"))
        self.assertEqual(result["profile"][1]["x"], 548001.0)
        self.assertAlmostEqual(result["profile"][2]["y"], 216003.66666666666)
        self.assertAlmostEqual(result["profile"][2]["values"]["dem"], 1155)
        self.assertAlmostEqual(result["profile"][2]["dist"], Decimal("5.2"))
        self.assertAlmostEqual(result["profile"][2]["x"], 548003.6666666666)
        self.assertAlmostEqual(result["profile"][3]["y"], 216006.33333333334)
        self.assertAlmostEqual(result["profile"][3]["values"]["dem"], 1154)
        self.assertAlmostEqual(result["profile"][3]["dist"], Decimal("9"))
        self.assertAlmostEqual(result["profile"][3]["x"], 548006.3333333334)
        self.assertAlmostEqual(result["profile"][4]["y"], 216009.0)
        self.assertAlmostEqual(result["profile"][4]["values"]["dem"], 1158)
        self.assertAlmostEqual(result["profile"][4]["dist"], Decimal("12.7"))
        self.assertAlmostEqual(result["profile"][4]["x"], 548009.0)

        # test wrong layer name
        request.params["layers"] = "wrong"
        self.assertRaises(HTTPNotFound, profile.json)

    def test_profile_csv(self):
        from pyramid.testing import DummyRequest
        from c2cgeoportal_geoportal.views.profile import Profile

        request = DummyRequest()
        request.registry.settings = {
            "raster": {
                "dem": {"file": "/src/geoportal/tests/data/dem.shp", "round": 1},
                "dem2": {"file": "/src/geoportal/tests/data/dem.shp", "round": 1},
                "dem4": {"file": "/src/geoportal/tests/data/dem4.shp", "round": 1}
            }
        }
        profile = Profile(request)

        request.params["nbPoints"] = "3"
        request.params["geom"] = '{"type":"LineString",' \
            '"coordinates":[[548009.5,215990],[547990,216009.5]]}'
        response = profile.csv()
        self.assertEqual(response.body.decode("utf-8"), """distance,dem,dem2,dem4,x,y
0.0,-9999,-9999,-9999,548009.5,215990.0
9.2,1181,1181,-9999,548003.0,215996.5
18.4,1180,1180,-9999,547996.5,216003.0
27.6,1164,1164,1164,547990.0,216009.5""")

        request.params["layers"] = "dem"
        response = profile.csv()
        self.assertEqual(response.body.decode("utf-8"), """distance,dem,x,y
0.0,-9999,548009.5,215990.0
9.2,1181,548003.0,215996.5
18.4,1180,547996.5,216003.0
27.6,1164,547990.0,216009.5""")
