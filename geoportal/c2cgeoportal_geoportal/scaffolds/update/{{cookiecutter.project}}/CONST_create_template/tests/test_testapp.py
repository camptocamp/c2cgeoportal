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

# This file should be used only on the test project in the c2cgeoportal CI

import re

import polib
import pytest
import requests


@pytest.mark.parametrize("test_number", [0, 1])
def test_po(test_number: int) -> None:
    """Tests that the generated pot files are identical between the command line and the view."""
    del test_number

    response = requests.get("https://front/locale.pot", verify=False, timeout=30)  # nosec
    assert response.status_code == 200, response.text
    response_keys = {e.msgid for e in polib.pofile(response.text)}

    with open(
        "geoportal/{{cookiecutter.package}}_geoportal/locale/{{cookiecutter.package}}_geoportal-client.pot",
        encoding="utf-8",
    ) as current_file:
        current_content = current_file.read()
        current_content_keys = {e.msgid for e in polib.pofile(current_content)}

    if response_keys != current_content_keys:
        assert response.text == current_content


@pytest.mark.parametrize("url", ["https://front/desktop_alt"])
def test_desktop_alt(url: str) -> None:
    """Tests the desktop alt page."""
    response = requests.get(url, verify=False, timeout=30)  # nosec
    assert response.status_code == 200, response.text

    assert re.search(
        r'<script src="https://front/static-ngeo-dist/desktop-.*\.js" crossorigin="anonymous"></script>',
        response.text,
    ), response.text
    assert re.search(r'<html lang="{{"{{mainCtrl.lang}}"}}" ', response.text), response.text


def test_enum() -> None:
    """Test the enumerations view."""
    response = requests.get("https://front/layers/test/values/type", verify=False, timeout=30)  # nosec
    assert response.status_code == 200, response.text

    assert response.json() == {"items": [{"value": "car"}, {"value": "train"}]}, response.text
