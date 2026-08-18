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

import time

import pytest
import requests


@pytest.mark.parametrize(
    ("url", "params", "timeout"),
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
        (
            "http://mapserver:8080/mapserv_proxy/MapServer",
            {"SERVICE": "WMS", "REQUEST": "GetCapabilities"},
            60,
        ),
        (
            "https://front/mapserv_proxy",
            {"ogcserver": "MapServer", "SERVICE": "WMS", "REQUEST": "GetCapabilities"},
            60,
        ),
        # (
        #     "http://qgisserver:8080/mapserv_proxy/",
        #     {"SERVICE": "WMS", "REQUEST": "GetCapabilities", "MAP": "/etc/qgisserver/project.qgs"},
        #     60,
        # ),
        # (
        #     "https://front/mapserv_proxy",
        #     {"ogcserver": "qgisserver", "SERVICE": "WMS", "REQUEST": "GetCapabilities"},
        #     60,
        # ),
        # OGC API - Features
        # (
        #     "http://mapserver:8080/mapserv_proxy/MapServer/ogcapi/collections/osm_protected/items",
        #     {"bbox": "6.0,46.0,7.0,47.0", "limit": "100"},
        #     60,
        # ),
        # (
        #     "https://front/mapserv_proxy/MapServer/ogcapi/collections/osm_open/items",
        #     {"bbox": "6.0,46.0,7.0,47.0", "limit": "100"},
        #     60,
        # ),
        # (
        #     "http://qgisserver:8080/mapserv_proxy/qgisserver/wfs3/collections/points/items",
        #     {"map": "/etc/qgisserver/project.qgs", "bbox": "6.0,46.0,7.0,47.0", "limit": "100"},
        #     60,
        # ),
        # (
        #     "https://front/mapserv_proxy/qgisserver/wfs3/collections/points/items",
        #     {"bbox": "6.0,46.0,7.0,47.0", "limit": "100"},
        #     60,
        # ),
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
