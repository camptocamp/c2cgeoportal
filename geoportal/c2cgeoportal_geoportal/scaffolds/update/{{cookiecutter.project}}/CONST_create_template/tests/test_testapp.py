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
    """Test the enumerations view"""
    response = requests.get("https://front/layers/test/values/type", verify=False, timeout=30)  # nosec
    assert response.status_code == 200, response.text

    assert response.json() == {"items": [{"value": "car"}, {"value": "train"}]}, response.text
