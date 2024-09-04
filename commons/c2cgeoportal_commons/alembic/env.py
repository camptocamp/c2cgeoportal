# Copyright (c) 2014-2024, Camptocamp SA
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


# pylint: disable=no-member

import logging.config
from typing import Any, cast

import sqlalchemy
from alembic import context
from c2c.template.config import config
from plaster.loaders import setup_logging
from sqlalchemy import engine_from_config, pool

_LOG = logging.getLogger(__name__)


# Interpret the config file for Python logging.
# This line sets up loggers basically.
setup_logging(context.config.config_file_name)


def get_config() -> dict[str, str | bool]:
    """Get the application configuration."""
    app_cfg = context.config.get_main_option("app.cfg")
    assert app_cfg is not None
    config.init(app_cfg)
    conf = config.get_config()
    assert conf is not None
    settings: dict[str, str | bool] = {}
    settings.update(conf)
    alembic_name = context.config.get_main_option("type")
    schema_postfix = f"_{alembic_name}" if alembic_name != "main" else ""
    schema_config_name = f"schema{schema_postfix}"
    script_location = context.config.get_main_option("script_location")
    version_table = context.config.get_main_option("version_table")
    version_locations = context.config.get_main_option("version_locations")
    assert script_location
    assert version_table
    assert version_locations
    settings.update(
        {
            "script_location": script_location,
            "version_table": version_table,
            "version_locations": version_locations,
            "version_table_schema": config[schema_config_name],
        }
    )
    return settings


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we do not even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    conf = get_config()
    context.configure(url=conf["sqlalchemy.url"], **conf)  # type: ignore

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with the context.
    """
    conf: dict[str, Any] = get_config()

    # Autogenerate config
    alembic_name = context.config.get_main_option("type")
    from c2cgeoportal_commons.models import Base, main, static  # pylint: disable=import-outside-toplevel

    _schema = main._schema if alembic_name == "main" else static._schema  # pylint: disable=protected-access

    def include_object(
        obj: sqlalchemy.ext.declarative.ConcreteBase,
        name: str,
        type_: str,
        reflected: str,
        compare_to: str,
    ) -> bool:
        del name, reflected, compare_to

        if type_ == "table":
            return cast(bool, obj.schema == _schema)  # type: ignore[attr-defined]
        return cast(bool, obj.table.schema == _schema)  # type: ignore[attr-defined]

    if _schema:
        conf.update(
            {"target_metadata": Base.metadata, "include_schemas": True, "include_object": include_object}
        )

    engine = engine_from_config(conf, prefix="sqlalchemy.", poolclass=pool.NullPool)
    connection = engine.connect()
    context.configure(connection=connection, **conf)

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
