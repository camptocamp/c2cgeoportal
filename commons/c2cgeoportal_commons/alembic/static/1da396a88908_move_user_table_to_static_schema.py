# Copyright (c) 2015-2025, Camptocamp SA
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

# pylint: disable=no-member,invalid-name

"""
Move user table to static schema.

Revision ID: 1da396a88908
Revises: 3f89a7d71a5e
Create Date: 2015-02-20 14:09:04.875390
"""

from hashlib import sha1

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Boolean, Integer, String, Unicode

# revision identifiers, used by Alembic.
revision = "1da396a88908"
down_revision = "3f89a7d71a5e"


def upgrade() -> None:
    """Upgrade."""
    schema = config["schema"]
    staticschema = config["schema_static"]
    parentschema = config.get("parentschema")

    engine = op.get_bind().engine
    with engine.connect() as connection:
        if type(engine).__name__ != "MockConnection" and op.get_context().dialect.has_table(
            connection,
            "user",
            schema=staticschema,
        ):
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
    parent_column = ""
    parent_select = ""
    parent_join = ""
    if parentschema is not None and parentschema != "":
        op.add_column("user", Column("parent_role_name", String), schema=staticschema)
        parent_column = ", parent_role_name"
        parent_select = ", pr.name"
        parent_join = f"LEFT OUTER JOIN {parentschema!s}.role AS pr ON (pr.id = u.parent_role_id)"

    try:
        op.execute(
            f"INSERT INTO {staticschema}.user "
            f"(type, username, password, email, is_password_changed, role_name{parent_column}) ("
            "SELECT u.type, u.username, u.password, u.email, "
            f"u.is_password_changed, r.name{parent_select} "
            f"FROM {schema}.user AS u "
            f"LEFT OUTER JOIN {schema}.role AS r ON (r.id = u.role_id) {parent_join}"
            ")",
        )
        op.drop_table("user", schema=schema)
    except Exception:  # pylint: disable=broad-exception-caught
        op.execute(
            "INSERT INTO %(staticschema)s.user (type, username, email, password, role) "  # noqa: UP031
            "VALUES ( 'user', 'admin', 'info@example.com', '%(pass)s', 'role_admin')"
            % {"staticschema": staticschema, "pass": sha1(b"admin").hexdigest()},  # nosec
        )


def downgrade() -> None:
    """Downgrade."""
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
    parent_column = ""
    parent_select = ""
    parent_join = ""
    if parentschema is not None and parentschema != "":
        op.add_column(
            "user",
            Column("parent_role_id", Integer, ForeignKey(parentschema + ".role.id")),
            schema=schema,
        )
        parent_column = ", parent_role_id"
        parent_select = ", pr.id"
        parent_join = f"LEFT OUTER JOIN {parentschema}.role AS pr ON (pr.name = u.parent_role_name)"

    op.execute(
        f"INSERT INTO {schema}.user "
        f"(type, username, password, email, is_password_changed, role_id{parent_column}) ("
        "SELECT u.type, u.username, u.password, u.email, "
        f"u.is_password_changed, r.id{parent_select} "
        f"FROM {staticschema}.user AS u "
        f"LEFT OUTER JOIN {schema}.role AS r ON (r.name = u.role_name) {parent_join}"
        ")",
    )

    op.drop_table("user", schema=staticschema)
