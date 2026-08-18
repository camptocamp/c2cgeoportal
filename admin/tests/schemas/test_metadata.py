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


import pytest


@pytest.mark.usefixtures("settings")
def test_get_relevant_for() -> None:
    from c2cgeoportal_admin.schemas.metadata import get_relevant_for
    from c2cgeoportal_commons.models.main import LayerGroup, LayerWMS

    assert get_relevant_for(LayerGroup) == {"layergroup", "treegroup", "treeitem"}
    assert get_relevant_for(LayerWMS) == {"layer_wms", "layer", "treeitem"}


def test_metadata_definitions() -> None:
    from c2cgeoportal_admin.schemas.metadata import (
        metadata_definitions,
    )
    from c2cgeoportal_commons.models.main import LayerGroup, LayerWMS

    settings = {
        "admin_interface": {
            "available_metadata": [
                {
                    "name": "empty",
                },
                {
                    "name": "treeitem",
                    "relevant_for": ["treeitem"],
                },
                {
                    "name": "layergroup",
                    "relevant_for": ["layergroup"],
                },
                {
                    "name": "layer",
                    "relevant_for": ["layer"],
                },
                {
                    "name": "layer_wms",
                    "relevant_for": ["layer_wms"],
                },
                {
                    "name": "layer_wms_and_wmts",
                    "relevant_for": ["layer_wms", "layer_wmts"],
                },
            ],
        },
    }

    assert [m["name"] for m in metadata_definitions(settings, LayerGroup)] == [
        "empty",
        "treeitem",
        "layergroup",
    ]

    assert [m["name"] for m in metadata_definitions(settings, LayerWMS)] == [
        "empty",
        "treeitem",
        "layer",
        "layer_wms",
        "layer_wms_and_wmts",
    ]
