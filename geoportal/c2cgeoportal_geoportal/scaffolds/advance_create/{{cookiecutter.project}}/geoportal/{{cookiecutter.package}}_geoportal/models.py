import logging

from c2cgeoportal_commons.models.main import *  # noqa: ignore=F401, pylint: disable=unused-wildcard-import
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory("{{cookiecutter.package}}_geoportal-server")
_LOG = logging.getLogger(__name__)
