# Copyright (c) 2020, Camptocamp SA
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

from unittest.mock import Mock, mock_open, patch

import pytest
import yaml
from c2c.template.config import config as configuration
from tests.functional import setup_common as setup_module

from c2cgeoportal_geoportal.lib.lingua_extractor import GeomapfishConfigExtractor

GMF_CONFIG = """
vars:
  interfaces_config:
    desktop:
      constants:
        gmfSearchOptions:
          datasources:

  admin_interface:
    available_metadata:
      - name: metadata1
        translate: true

  raster:
    raster1:

  dbsessions:
    db1:
      url: postgresql://www-data:www-data@db:5432/geomapfish_tests

  layers:
    enum:
      layer1:
        attributes:
          name:
            table: geodata.testpoint
"""


@pytest.fixture(scope="module")
def settings():
    setup_module()

    settings = {
        **configuration.get_config(),
        **yaml.load(GMF_CONFIG, Loader=yaml.BaseLoader)["vars"],
    }

    with patch(
        "c2c.template.get_config",
        return_value=settings,
    ):
        yield settings


@pytest.fixture(scope="module")
def dbsession(settings):
    from c2cgeoportal_commons.models import DBSession, DBSessions

    DBSessions["db1"] = DBSession

    with patch("c2cgeoportal_geoportal.init_db_sessions"):
        yield DBSession


@pytest.fixture(scope="function")
def transact(dbsession):
    t = dbsession.begin_nested()
    yield t
    t.rollback()
    dbsession.expire_all()


@pytest.fixture(scope="function")
def test_data(dbsession, transact):
    from sqlalchemy import text

    from c2cgeoportal_commons.models import main

    dbsession.execute(
        text(
            """
INSERT INTO geodata.testpoint (name)
VALUES ('testpoint_name1');
"""
        )
    )

    theme = main.Theme(name="test_theme")
    theme.metadatas = [
        main.Metadata(
            name="metadata1",
            value="metadata1_value",
        )
    ]
    dbsession.add(theme)
    dbsession.flush()


@pytest.mark.usefixtures("test_data")
class TestGeomapfishConfigExtractor:
    @patch(
        "c2cgeoportal_geoportal.lib.lingua_extractor.open",
        mock_open(read_data="vars:"),
    )
    def test_extract_config(self, settings, dbsession):
        extractor = GeomapfishConfigExtractor()

        options = Mock()
        options.keywords = []

        messages = list(extractor("config.yaml", options))

        assert {msg.msgid for msg in messages} == {"raster1", "testpoint_name1", "metadata1_value"}
