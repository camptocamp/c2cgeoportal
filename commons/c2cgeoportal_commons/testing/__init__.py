# Copyright (c) 2018-2024, Camptocamp SA
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


from typing import Any

import zope.sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, configure_mappers, sessionmaker
from transaction import TransactionManager


def get_engine(settings: dict[str, Any], prefix: str = "sqlalchemy.") -> Engine:
    """Get the engine."""
    return engine_from_config(settings, prefix)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:  # pylint: disable=unsubscriptable-object
    """Get the session factory."""
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(
    session_factory: sessionmaker[Session],  # pylint: disable=unsubscriptable-object
    transaction_manager: TransactionManager,
) -> Session:
    """
    Get a ``sqlalchemy.orm.Session`` instance backed by a transaction.

    This function will hook the session to the transaction manager which
    will take care of committing any changes.

    - When using pyramid_tm it will automatically be committed or aborted
      depending on whether an exception is raised.

    - When using scripts you should wrap the session in a manager yourself.
      For example::

          import transaction

          engine = get_engine(settings)
          session_factory = get_session_factory(engine)
          with transaction.manager:
              dbsession = get_tm_session(session_factory, transaction.manager)
    """
    dbsession = session_factory()
    assert isinstance(dbsession, Session)
    zope.sqlalchemy.register(dbsession, transaction_manager=transaction_manager)
    return dbsession


def generate_mappers() -> None:
    """Initialize the model for a Pyramid app."""

    # import or define all models here to ensure they are attached to the
    # Base.metadata prior to any initialization routines
    import c2cgeoportal_commons.models.main  # pylint: disable=unused-import,import-outside-toplevel
    import c2cgeoportal_commons.models.static  # pylint: disable=import-outside-toplevel

    # run configure_mappers after defining all of the models to ensure
    # all relationships can be setup
    configure_mappers()


def get_session(
    settings: dict[str, Any], transaction_manager: TransactionManager, prefix: str = "sqlalchemy."
) -> Session:
    """Get the session."""
    configure_mappers()
    engine = get_engine(settings, prefix)
    session_factory = get_session_factory(engine)
    return get_tm_session(session_factory, transaction_manager)
