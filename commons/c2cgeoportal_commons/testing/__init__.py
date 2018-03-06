# -*- coding: utf-8 -*-

from transaction import TransactionManager
import zope.sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, configure_mappers


def get_engine(settings: dict, prefix: str='sqlalchemy.') -> Engine:
    return engine_from_config(settings, prefix)


def get_session_factory(engine: Engine) -> sessionmaker:
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory: sessionmaker, transaction_manager: TransactionManager) -> Session:
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
    zope.sqlalchemy.register(
        dbsession, transaction_manager=transaction_manager)
    return dbsession


def generate_mappers() -> None:
    """
    Initialize the model for a Pyramid app.
    """

    # import or define all models here to ensure they are attached to the
    # Base.metadata prior to any initialization routines
    import c2cgeoportal_commons.models.main  # flake8: noqa

    # run configure_mappers after defining all of the models to ensure
    # all relationships can be setup
    configure_mappers()
