# Copyright (c) 2025-2026, Camptocamp SA
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


from unittest import TestCase
from unittest.mock import patch

from c2cgeoportal_geoportal.lib.i18n import available_locale_names

example_locale_content = {
    ("de", True),
    ("en", True),
    ("fr", True),
    (".emptyfolder", False),
    ("geomapfish_geoportal-client.pot", False),
}


class TestI18n(TestCase):
    @patch("c2cgeoportal_geoportal.lib.i18n.os.path.exists", return_value=True)
    @patch(
        "c2cgeoportal_geoportal.lib.i18n.os.listdir",
        return_value=[locale[0] for locale in example_locale_content],
    )
    @patch(
        "c2cgeoportal_geoportal.lib.i18n.os.path.isdir",
        side_effect=[locale[1] for locale in example_locale_content],
    )
    def test_available_locale_names(self, isdir_mock, listdir_mock, exists_mock) -> None:
        locales = available_locale_names()
        assert set(locales) == {"de", "en", "fr"}

    def test_available_locale_names_no_dir(self) -> None:
        locales = available_locale_names()
        assert locales == []
