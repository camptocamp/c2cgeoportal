import pytest


@pytest.mark.usefixtures("settings")
def test_functionality_definitions() -> None:
    from c2cgeoportal_admin.schemas.functionalities import available_functionalities_for
    from c2cgeoportal_commons.models.main import Role, Theme

    settings = {
        "admin_interface": {
            "available_functionalities": [
                {
                    "name": "empty",
                },
                {
                    "name": "role",
                    "relevant_for": ["role"],
                },
                {
                    "name": "theme",
                    "relevant_for": ["theme"],
                },
            ],
        },
    }

    assert [m["name"] for m in available_functionalities_for(settings, Theme)] == [
        "empty",
        "theme",
    ]

    assert [m["name"] for m in available_functionalities_for(settings, Role)] == [
        "empty",
        "role",
    ]
