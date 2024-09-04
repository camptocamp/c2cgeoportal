# Copyright (c) 2022-2024, Camptocamp SA
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

from c2cgeoportal_admin.lib.lingva_extractor import GeomapfishConfigExtractor

GMF_CONFIG = """
vars:
  admin_interface:
    available_metadata:
      - name: metadata1
        description: description1
        translate: true
    available_functionalities:
      - name: functionality1
        description: description2
"""


class TestGeomapfishConfigExtractor:
    @patch(
        "c2cgeoportal_admin.lib.lingva_extractor.open",
        mock_open(read_data=GMF_CONFIG),
    )
    def test_extract_config(self):
        extractor = GeomapfishConfigExtractor()

        options = Mock()
        options.keywords = []

        messages = list(extractor("config.yaml", options))

        assert {msg.msgid for msg in messages} == {"description1", "description2"}
