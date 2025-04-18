# Copyright (c) 2013-2025, Camptocamp SA
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


from io import StringIO
from unittest import TestCase
from xml import sax
from xml.sax.saxutils import XMLGenerator

from tests import load_file
from tests.functional import setup_common as setup_module  # noqa
from tests.functional import teardown_common as teardown_module  # noqa


class TestFilterCapabilities(TestCase):
    capabilities_file = "tests/data/tinyows_getcapabilities.xml"

    def test_capabilities_filter_featuretype(self) -> None:
        xml = load_file(TestFilterCapabilities.capabilities_file)
        layers_whitelist = set()
        filtered_xml = self._filter_xml(xml, "FeatureType", layers_whitelist)

        assert "<Name>tows:parks</Name>" not in filtered_xml

    def test_capabilities_filter_featuretype_private_layer(self) -> None:
        xml = load_file(TestFilterCapabilities.capabilities_file)
        layers_whitelist = set()
        layers_whitelist.add("parks")
        filtered_xml = self._filter_xml(xml, "FeatureType", layers_whitelist)

        assert "<Name>tows:parks</Name>" in filtered_xml

    @staticmethod
    def _filter_xml(xml, tag_name, layers_whitelist):
        from c2cgeoportal_geoportal.lib.filter_capabilities import _CapabilitiesFilter

        parser = sax.make_parser()
        result = StringIO()
        downstream_handler = XMLGenerator(result, "utf-8")
        filter_handler = _CapabilitiesFilter(
            parser,
            downstream_handler,
            tag_name,
            layers_whitelist=layers_whitelist,
        )
        filter_handler.parse(StringIO(xml))
        return result.getvalue()
