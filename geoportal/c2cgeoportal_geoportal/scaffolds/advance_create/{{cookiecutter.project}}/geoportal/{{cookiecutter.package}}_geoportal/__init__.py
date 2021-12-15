import distutils.core

from pyramid.config import Configurator

import {{cookiecutter.package}}_geoportal.authentication
import {{cookiecutter.package}}_geoportal.dev
import {{cookiecutter.package}}_geoportal.multi_organization
from c2cgeoportal_geoportal import INTERFACE_TYPE_NGEO, add_interface_config, locale_negotiator
from c2cgeoportal_geoportal.lib.i18n import LOCALE_PATH
from {{cookiecutter.package}}_geoportal.resources import Root


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    del global_config  # Unused

    config = Configurator(
        root_factory=Root,
        settings=settings,
        locale_negotiator=locale_negotiator,
    )

    config.include("c2cgeoportal_commons")

    config.include({{cookiecutter.package}}_geoportal.authentication.includeme)

    config.add_translation_dirs(LOCALE_PATH)

    # Workaround to not have the error: distutils.errors.DistutilsArgError: no commands supplied
    distutils.core._setup_stop_after = "config"  # pylint: disable=protected-access
    config.include("c2cgeoportal_geoportal")
    distutils.core._setup_stop_after = None  # pylint: disable=protected-access

    config.include({{cookiecutter.package}}_geoportal.multi_organization.includeme)

    # Scan view decorator for adding routes
    config.scan()

    # Add the interfaces
    for interface in config.get_settings().get("interfaces", []):
        add_interface_config(config, interface)

    config.include({{cookiecutter.package}}_geoportal.dev.includeme)

    return config.make_wsgi_app()
