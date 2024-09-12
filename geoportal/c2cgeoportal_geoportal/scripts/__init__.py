# Copyright (c) 2011-2024, Camptocamp SA
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


import os
from argparse import ArgumentParser, Namespace
from typing import Any

import c2cwsgiutils.setup_process
import pyramid.config
import transaction
import zope.sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy.orm import Session, configure_mappers, sessionmaker


def fill_arguments(parser: ArgumentParser, use_attribute: bool = False) -> None:
    """Fill the command line argument description."""
    default_config_uri = (
        "c2c://development.ini" if os.path.isfile("development.ini") else "c2c://geoportal/development.ini"
    )
    c2cwsgiutils.setup_process.fill_arguments(
        parser, default_config_uri=default_config_uri, use_attribute=use_attribute
    )


def get_appsettings(options: Namespace) -> pyramid.config.Configurator:
    """Get the application settings."""
    return c2cwsgiutils.setup_process.bootstrap_application_from_options(options)["registry"].settings


def get_session(settings: dict[str, Any], transaction_manager: transaction.TransactionManager) -> Session:
    """Get the database session in script context."""
    configure_mappers()
    engine = engine_from_config(settings)
    session_factory = sessionmaker()
    session_factory.configure(bind=engine)
    dbsession = session_factory()
    zope.sqlalchemy.register(dbsession, transaction_manager=transaction_manager)
    return dbsession
