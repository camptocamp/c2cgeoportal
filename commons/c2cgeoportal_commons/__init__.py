"""c2cgeoportal_commons package."""
from typing import Optional  # noqa, pylint: disable=unused-import

from c2c.template.config import config as configuration
from pyramid.config import Configurator


def includeme(config: Configurator) -> None:
    """
    Initialize the model for a Pyramid app.
    Activate this setup using ``config.include('c2cgeoportal_admin.commons')``.
    """
    settings = config.get_settings()

    configuration.init(settings.get("app.cfg"))
    # Update the settings object from the YAML application config file
    settings.update(configuration.get_config())
