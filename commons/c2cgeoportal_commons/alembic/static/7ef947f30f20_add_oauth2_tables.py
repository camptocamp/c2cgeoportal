# Copyright (c) 2020-2024, Camptocamp SA
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

# pylint: disable=invalid-name

"""
Add OAuth2 tables.

Revision ID: 7ef947f30f20
Revises: 107b81f5b9fe
Create Date: 2021-03-09 17:09:54.737275
"""

import sqlalchemy.schema
from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import DateTime, Integer, Unicode

# revision identifiers, used by Alembic.
revision = "7ef947f30f20"
down_revision = "107b81f5b9fe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    staticschema = config["schema_static"]

    # Instructions
    op.create_table(
        "oauth2_client",
        Column("id", Integer, primary_key=True),
        Column("client_id", Unicode, unique=True),
        Column("secret", Unicode),
        Column("redirect_uri", Unicode),
        schema=staticschema,
    )
    op.create_table(
        "oauth2_bearertoken",
        Column("id", Integer, primary_key=True),
        Column(
            "client_id",
            Integer,
            ForeignKey(staticschema + ".oauth2_client.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column(
            "user_id",
            Integer,
            ForeignKey(staticschema + ".user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("access_token", Unicode(100), unique=True),
        Column("refresh_token", Unicode(100), unique=True),
        Column("expire_at", DateTime(timezone=True)),
        sqlalchemy.schema.UniqueConstraint("client_id", "user_id"),
        schema=staticschema,
    )
    op.create_table(
        "oauth2_authorizationcode",
        Column("id", Integer, primary_key=True),
        Column(
            "client_id",
            Integer,
            ForeignKey(staticschema + ".oauth2_client.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column(
            "user_id",
            Integer,
            ForeignKey(staticschema + ".user.id", ondelete="CASCADE"),
            nullable=False,
        ),
        Column("redirect_uri", Unicode),
        Column("code", Unicode(100), unique=True),
        Column("expire_at", DateTime(timezone=True)),
        sqlalchemy.schema.UniqueConstraint("client_id", "user_id"),
        schema=staticschema,
    )


def downgrade() -> None:
    """Downgrade."""
    staticschema = config["schema_static"]

    # Instructions
    op.drop_table("oauth2_bearertoken", schema=staticschema)
    op.drop_table("oauth2_authorizationcode", schema=staticschema)
    op.drop_table("oauth2_client", schema=staticschema)
