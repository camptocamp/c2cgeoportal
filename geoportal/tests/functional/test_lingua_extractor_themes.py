# Copyright (c) 2020-2024, Camptocamp SA
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

# pylint: disable=missing-docstring

from unittest.mock import Mock

import pytest

from c2cgeoportal_geoportal.lib.lingua_extractor import GeomapfishThemeExtractor


class TestGeomapfishThemeExtractor:
    def extract(self):
        extractor = GeomapfishThemeExtractor()
        extractor.config = {"lingua_extractor": {}}

        options = Mock()
        options.keywords = []

        return list(extractor("development.ini", options))

    def test_extract_theme(self, dbsession, transact):
        from c2cgeoportal_commons.models import main

        del transact

        theme = main.Theme(name="theme")
        dbsession.add(theme)
        dbsession.flush()

        messages = self.extract()

        assert {m.msgid for m in messages} == {"theme"}

    def test_extract_group(self, dbsession, transact):
        from c2cgeoportal_commons.models import main

        del transact

        group = main.LayerGroup(name="group")
        dbsession.add(group)
        dbsession.flush()

        messages = self.extract()

        assert {m.msgid for m in messages} == {"group"}

    def test_extract_layer_wms(self, dbsession, transact):
        from c2cgeoportal_commons.models import main

        del transact

        ogc_server = main.OGCServer(name="mapserver", url="http://mapserver:8080")
        layer_wms = main.LayerWMS(name="layer_wms")
        layer_wms.ogc_server = ogc_server
        layer_wms.layer = "testpoint_unprotected"
        dbsession.add(layer_wms)
        dbsession.flush()

        messages = self.extract()

        assert {m.msgid for m in messages} == {
            "layer_wms",
            "testpoint_unprotected",
            "city",
            "country",
            "name",
        }

    def test_extract_layer_wmts(self, dbsession, transact):
        from c2cgeoportal_commons.models import main

        del transact

        ogc_server = main.OGCServer(name="mapserver", url="http://mapserver:8080")
        layer_wmts = main.LayerWMTS(name="layer_wmts")
        layer_wmts.url = "https://example.com"
        layer_wmts.layer = "mylayer"
        layer_wmts.metadatas = [
            main.Metadata("ogcServer", "mapserver"),
            main.Metadata("queryLayers", "testpoint_protected"),
        ]
        dbsession.add_all([ogc_server, layer_wmts])
        dbsession.flush()

        messages = self.extract()

        assert {m.msgid for m in messages} == {
            "layer_wmts",
            "testpoint_protected",
            "city",
            "country",
            "name",
        }

    def test_extract_full_text_search(self, dbsession, transact):
        from c2cgeoportal_commons.models import main

        del transact

        fts = main.FullTextSearch()
        fts.label = "label"
        fts.layer_name = "some_layer_name"
        fts.actions = [{"action": "add_layer", "data": "another_layer_name"}]
        dbsession.add(fts)
        dbsession.flush()

        messages = self.extract()

        assert {m.msgid for m in messages} == {
            "some_layer_name",
            "another_layer_name",
        }
