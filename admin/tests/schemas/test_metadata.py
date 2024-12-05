import pytest


@pytest.mark.usefixtures("settings")
def test_get_relevant_for():
    from c2cgeoportal_admin.schemas.metadata import get_relevant_for
    from c2cgeoportal_commons.models.main import LayerGroup, LayerWMS

    assert get_relevant_for(LayerGroup) == {"layergroup", "treegroup", "treeitem"}
    assert get_relevant_for(LayerWMS) == {"layer_wms", "layer", "treeitem"}


def test_metadata_definitions():
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
            ]
        }
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
