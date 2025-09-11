import logging

from c2cgeoportal_commons.models.main import *  # pylint: disable=unused-wildcard-import # noqa: F403
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory("{{cookiecutter.package}}_geoportal-server")
_LOG = logging.getLogger(__name__)
