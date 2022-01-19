# Copyright (c) 2011-2021, Camptocamp SA
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

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import argparse
import os
from argparse import ArgumentParser, Namespace
from typing import Any, Callable, Dict, Optional, TypedDict, cast

import pyramid.config
import transaction
import zope.sqlalchemy
from pyramid.paster import bootstrap
from pyramid.scripts.common import get_config_loader, parse_vars
from sqlalchemy import engine_from_config
from sqlalchemy.orm import Session, configure_mappers, sessionmaker

# import c2cwsgiutils.setup_process
# TODO remove on next c2c wsgi utils release


def fill_arguments_(
    parser: argparse.ArgumentParser,
    config_vars_attrubute: bool = False,
    default_config_uri: Optional[str] = None,
) -> None:
    """Add the needed arguments to the parser like it's don in pshell."""

    parser.add_argument(
        "config_uri",
        nargs="?",
        default=default_config_uri,
        help="The URI to the configuration file.",
    )
    parser.add_argument(
        "--config-vars" if config_vars_attrubute else "config_vars",
        nargs="*",
        default=(),
        help="Variables required by the config file. For example, "
        "`http_port=%%(http_port)s` would expect `http_port=8080` to be "
        "passed here.",
    )


PyramidEnv = TypedDict(
    "PyramidEnv",
    {
        "root": Any,
        "closer": Callable[..., Any],
        "registry": pyramid.registry.Registry,
        "request": pyramid.request.Request,
        "root_factory": object,
        "app": Callable[[Dict[str, str], Any], Any],
    },
    total=True,
)


def bootstrap_application_options(options: argparse.Namespace) -> PyramidEnv:
    """
    Initialize all the application from the command line arguments.

    :return: This function returns a dictionary as in bootstrap, see:
    https://docs.pylonsproject.org/projects/pyramid/en/latest/api/paster.html?highlight=bootstrap#pyramid.paster.bootstrap
    """
    return bootstrap_application(
        options.config_uri, parse_vars(options.config_vars) if options.config_vars else None
    )


def bootstrap_application(
    config_uri: str = "c2c:///app/development.ini",
    options: Optional[Dict[str, Any]] = None,
) -> PyramidEnv:
    """
    Initialize all the application.

    :return: This function returns a dictionary as in bootstrap, see:
    https://docs.pylonsproject.org/projects/pyramid/en/latest/api/paster.html?highlight=bootstrap#pyramid.paster.bootstrap
    """
    loader = get_config_loader(config_uri)
    loader.setup_logging(options)
    return cast(PyramidEnv, bootstrap(config_uri, options=options))


# End TODO remove


def fill_arguments(parser: ArgumentParser) -> None:
    """Fill the command line argument description."""
    default_config_uri = (
        "c2c://development.ini" if os.path.isfile("development.ini") else "c2c://geoportal/development.ini"
    )
    fill_arguments_(parser, default_config_uri=default_config_uri)


def get_appsettings(options: Namespace) -> pyramid.config.Configurator:
    """Get the application settings."""
    return bootstrap_application_options(options)["registry"].settings


def get_session(settings: Dict[str, Any], transaction_manager: transaction.TransactionManager) -> Session:
    """Get the database session in script context."""
    configure_mappers()
    engine = engine_from_config(settings)
    session_factory = sessionmaker()
    session_factory.configure(bind=engine)
    dbsession = session_factory()
    zope.sqlalchemy.register(dbsession, transaction_manager=transaction_manager)
    return dbsession
