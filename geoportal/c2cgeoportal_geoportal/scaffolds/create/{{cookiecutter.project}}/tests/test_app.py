import time
from typing import Dict

import pytest
import requests


@pytest.mark.parametrize(
    "url,params",
    [
        ("https://front", {}),
        ("https://front/themes", {}),
        ("https://front/static-geomapfish/0/locales/fr.json", {}),
        ("https://front/dynamic.json", {"interface": "desktop"}),
        ("https://front/dynamic.json", {"interface": "desktop", "query": "", "path": "/"}),
        ("https://front/c2c/health_check", {}),
        ("https://front/c2c/health_check", {"max_level": "1"}),
        ("https://front/c2c/health_check", {"checker": "check_collector"}),
        ("https://front/admin/layertree", {}),
        ("https://front/admin/layertree/children", {}),
        ("http://mapserver:8080/mapserv_proxy", {"SERVICE": "WMS", "REQUEST": "GetCapabilities"}),
        (
            "https://front/mapserv_proxy",
            {"ogcserver": "source for image/png", "SERVICE": "WMS", "REQUEST": "GetCapabilities"},
        ),
    ],
)
def test_url(url: str, params: Dict[str, str]) -> None:
    """Tests that some URL didn't return an error."""
    for _ in range(60):
        response = requests.get(url, params=params, verify=False, timeout=240)  # nosec
        if response.status_code == 503:
            time.sleep(1)
            continue
        break
    assert response.status_code == 200, response.text


def test_admin() -> None:
    """Tests that the admin page will provide the login page."""
    response = requests.get("https://front/admin/", verify=False, timeout=240)  # nosec
    assert response.status_code == 200, response.text
    assert "Login" in response.text
