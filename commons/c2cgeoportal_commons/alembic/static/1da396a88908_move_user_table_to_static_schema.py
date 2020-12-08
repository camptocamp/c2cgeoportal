# -*- coding: utf-8 -*-

# Copyright (c) 2015-2019, Camptocamp SA
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


"""Move user table to static schema

Revision ID: 1da396a88908
Revises: 3f89a7d71a5e
Create Date: 2015-02-20 14:09:04.875390
"""

from hashlib import sha1

import sqlalchemy
from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Boolean, Integer, String, Unicode

# revision identifiers, used by Alembic.
revision = "1da396a88908"
down_revision = "3f89a7d71a5e"


def upgrade():
    schema = config["schema"]
    staticschema = config["schema_static"]
    parentschema = config.get("parentschema")

    engine = op.get_bind().engine
    if type(engine).__name__ != "MockConnection" and op.get_context().dialect.has_table(
        engine, "user", schema=staticschema
    ):  # pragma: no cover
        return

    op.create_table(
        "user",
        Column("type", String(10), nullable=False),
        Column("id", Integer, primary_key=True),
        Column("username", Unicode, unique=True, nullable=False),
        Column("password", Unicode, nullable=False),
        Column("email", Unicode, nullable=False),
        Column("is_password_changed", Boolean, default=False),
        Column("role_name", String),
        schema=staticschema,
    )

    try:
        if parentschema is not None and parentschema != "":  # pragma: no cover
            op.execute(
                sqlalchemy.sql.text(
                    "INSERT INTO :staticschema.user "
                    "(type, username, password, email, is_password_changed, role_name, parent_role_name) ("
                    "SELECT u.type, u.username, u.password, u.email, "
                    "u.is_password_changed, r.name, pr.name "
                    "FROM :schema.user AS u "
                    "LEFT OUTER JOIN :schema.role AS r ON (r.id = u.role_id) "
                    "LEFT OUTER JOIN :parentschema.role AS pr ON (pr.id = u.parent_role_id)"
                    ")"
                ),
                staticschema=staticschema,
                schema=schema,
                parentschema=parentschema,
            )
        else:
            op.execute(
                sqlalchemy.sql.text(
                    "INSERT INTO :staticschema.user "
                    "(type, username, password, email, is_password_changed, role_name) ("
                    "SELECT u.type, u.username, u.password, u.email, "
                    "u.is_password_changed, r.name "
                    "FROM :schema.user AS u "
                    "LEFT OUTER JOIN :schema.role AS r ON (r.id = u.role_id) "
                    ")"
                ),
                staticschema=staticschema,
                schema=schema,
            )
        op.drop_table("user", schema=schema)
    except Exception:
        op.execute(
            sqlalchemy.sql.text(
                "INSERT INTO :staticschema.user (type, username, email, password, role) "
                "VALUES ('user', 'admin', 'info@example.com', :password, 'role_admin')"
            ),
            staticschema=staticschema,
            password=sha1("admin".encode("utf-8")).hexdigest(),
        )


def downgrade():
    schema = config["schema"]
    staticschema = config.get("schema_static")
    parentschema = config.get("parentschema")

    op.create_table(
        "user",
        Column("type", String(10), nullable=False),
        Column("id", Integer, primary_key=True),
        Column("username", Unicode, unique=True, nullable=False),
        Column("password", Unicode, nullable=False),
        Column("email", Unicode, nullable=False),
        Column("is_password_changed", Boolean, default=False),
        Column("role_id", Integer, ForeignKey(schema + ".role.id"), nullable=False),
        schema=schema,
    )
    if parentschema is not None and parentschema != "":  # pragma: no cover
        op.add_column(
            "user", Column("parent_role_id", Integer, ForeignKey(parentschema + ".role.id")), schema=schema
        )
        op.execute(
            sqlalchemy.sql.text(
                "INSERT INTO :schema.user "
                "(type, username, password, email, is_password_changed, role_id, parent_role_id) ("
                "SELECT u.type, u.username, u.password, u.email, "
                "u.is_password_changed, r.id, pr.id "
                "FROM :staticschema.user AS u "
                "LEFT OUTER JOIN :schema.role AS r ON (r.name = u.role_name) "
                "LEFT OUTER JOIN :parentschema.role AS pr ON (pr.name = u.parent_role_name) "
                ")"
            ),
            staticschema=staticschema,
            schema=schema,
            parentschema=parentschema,
        )
    else:
        op.execute(
            sqlalchemy.sql.text(
                "INSERT INTO :schema.user "
                "(type, username, password, email, is_password_changed, role_id) ("
                "SELECT u.type, u.username, u.password, u.email, "
                "u.is_password_changed, r.id "
                "FROM :staticschema.user AS u "
                "LEFT OUTER JOIN :schema.role AS r ON (r.name = u.role_name) "
                ")"
            ),
            staticschema=staticschema,
            schema=schema,
        )

    op.drop_table("user", schema=staticschema)
