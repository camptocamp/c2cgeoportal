# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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


import re
import logging
import sqlalchemy.ext.declarative
from sqlalchemy.orm import sessionmaker, configure_mappers
import zope.sqlalchemy
import c2cwsgiutils
import c2cgeoportal_commons.models

LOG = logging.getLogger(__name__)

DBSession = None  # Initialized by init_dbsessions
Base = sqlalchemy.ext.declarative.declarative_base()
DBSessions = {}

srid = None
schema = None


def get_engine(settings, prefix='sqlalchemy.'):
    return sqlalchemy.engine_from_config(settings, prefix)


def get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory, transaction_manager):
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


def generate_mappers(settings):
    """
    Initialize the model for a Pyramid app.
    """
    global schema
    schema = settings.get('schema')
    global srid
    srid = settings.get('srid')

    # import or define all models here to ensure they are attached to the
    # Base.metadata prior to any initialization routines
    from . import main  # flake8: noqa

    # run configure_mappers after defining all of the models to ensure
    # all relationships can be setup
    configure_mappers()

def init_dbsessions(settings, config=None, health_check=None):
    # define the srid, schema as global variables to be usable in the model
    global schema
    global srid
    srid = settings["srid"]
    schema = settings["schema"]

    db_chooser = settings.get("db_chooser", {})
    master_paths = [re.compile(i.replace("//", "/")) for i in db_chooser.get("master", [])]
    slave_paths = [re.compile(i.replace("//", "/")) for i in db_chooser.get("slave", [])]

    slave_prefix = "sqlalchemy_slave" if "sqlalchemy_slave.url" in settings else None

    c2cgeoportal_commons.models.DBSession, rw_bind, _ = c2cwsgiutils.db.setup_session(
        config, "sqlalchemy", slave_prefix, force_master=master_paths, force_slave=slave_paths)
    c2cgeoportal_commons.models.Base.metadata.bind = rw_bind
    c2cgeoportal_commons.models.DBSessions["dbsession"] = c2cgeoportal_commons.models.DBSession

    for dbsession_name, dbsession_config in settings.get("dbsessions", {}).items():  # pragma: nocover
        c2cgeoportal_commons.models.DBSessions[dbsession_name] = \
            c2cwsgiutils.db.create_session(config, dbsession_name, **dbsession_config)

    from c2cgeoportal_commons.models import main

    if health_check is not None:
        for name, session in c2cgeoportal_commons.models.DBSessions.items():
            if name == "dbsession":
                health_check.add_db_session_check(session, at_least_one_model=main.Theme)
            else:  # pragma: no cover
                health_check.add_db_session_check(
                    session, query_cb=lambda session: session.execute("SELECT 1"))
