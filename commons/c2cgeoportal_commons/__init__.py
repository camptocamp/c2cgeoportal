"""c2cgeoportal_commons package."""
from typing import Optional  # noqa, pylint: disable=unused-import

from pyramid.config import Configurator

from c2cgeoportal_commons.config import config as configuration


def includeme(config: Configurator) -> None:
    settings = config.get_settings()

    configuration.init(settings.get('app.cfg'))
    # update the settings object from the YAML application config file
    settings.update(configuration.get_config())
