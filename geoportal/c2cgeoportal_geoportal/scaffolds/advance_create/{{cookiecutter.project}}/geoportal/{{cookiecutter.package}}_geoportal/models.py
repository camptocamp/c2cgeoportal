import logging

from pyramid.i18n import TranslationStringFactory

from c2cgeoportal_commons.models.main import *  # pylint: disable=unused-wildcard-import

_ = TranslationStringFactory("{{cookiecutter.package}}_geoportal-server")
_LOG = logging.getLogger(__name__)
