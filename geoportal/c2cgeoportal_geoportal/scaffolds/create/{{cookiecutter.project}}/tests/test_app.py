import time

import pytest
import requests


@pytest.mark.parametrize(
    "url,params,timeout",
    [
        ("https://front/", {}, 10),
        ("https://front/themes", {}, 120),
        ("https://front/static-geomapfish/0/locales/fr.json", {}, 2),
        ("https://front/dynamic.json", {"interface": "desktop"}, 10),
        ("https://front/dynamic.json", {"interface": "desktop", "query": "", "path": "/"}, 10),
        ("https://front/c2c/health_check", {}, 2),
        ("https://front/c2c/health_check", {"max_level": "1"}, 2),
        ("https://front/c2c/health_check", {"checker": "check_collector"}, 2),
        ("https://front/admin/layertree", {}, 10),
        ("https://front/admin/layertree/children", {}, 10),
        ("http://mapserver:8080/mapserv_proxy", {"SERVICE": "WMS", "REQUEST": "GetCapabilities"}, 60),
        (
            "https://front/mapserv_proxy",
            {"ogcserver": "source for image/png", "SERVICE": "WMS", "REQUEST": "GetCapabilities"},
            60,
        ),
    ],
)
def test_url(url: str, params: dict[str, str], timeout: int) -> None:
    """Tests that some URL didn't return an error."""
    for _ in range(6):
        response = requests.get(url, params=params, verify=False, timeout=timeout)  # nosec
        if response.status_code == 503:
            time.sleep(1)
            continue
        break
    assert response.status_code == 200, response.text


def test_admin() -> None:
    """Tests that the admin page will provide the login page."""
    response = requests.get("https://front/admin/", verify=False, timeout=30)  # nosec
    assert response.status_code == 200, response.text
    assert "Login" in response.text
