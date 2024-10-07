# Copyright (c) 2024, Camptocamp SA
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
Sync the model and the database.

Revision ID: 910b4ca53b68
Revises: 76d72fb3fcb9
Create Date: 2024-04-22 07:17:27.468564
"""

import sqlalchemy as sa
from alembic import op
from c2c.template.config import config
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "910b4ca53b68"
down_revision = "76d72fb3fcb9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    staticschema = config["schema_static"]

    # Add required fields in oauth2
    op.alter_column(
        "oauth2_authorizationcode",
        "redirect_uri",
        existing_type=sa.VARCHAR(),
        nullable=False,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_authorizationcode",
        "expire_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_bearertoken",
        "access_token",
        existing_type=sa.VARCHAR(length=100),
        nullable=False,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_bearertoken",
        "refresh_token",
        existing_type=sa.VARCHAR(length=100),
        nullable=False,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_bearertoken",
        "expire_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=False,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_client", "client_id", existing_type=sa.VARCHAR(), nullable=False, schema=staticschema
    )
    op.alter_column(
        "oauth2_client", "secret", existing_type=sa.VARCHAR(), nullable=False, schema=staticschema
    )
    op.alter_column(
        "oauth2_client", "redirect_uri", existing_type=sa.VARCHAR(), nullable=False, schema=staticschema
    )
    op.execute(f"UPDATE {staticschema}.oauth2_client SET state_required = true WHERE state_required IS NULL")
    op.alter_column(
        "oauth2_client", "state_required", existing_type=sa.BOOLEAN(), nullable=False, schema=staticschema
    )
    op.execute(f"UPDATE {staticschema}.oauth2_client SET pkce_required = true WHERE pkce_required IS NULL")
    op.alter_column(
        "oauth2_client", "pkce_required", existing_type=sa.BOOLEAN(), nullable=False, schema=staticschema
    )
    # URL and creation are required
    op.alter_column("shorturl", "url", existing_type=sa.VARCHAR(), nullable=False, schema=staticschema)
    op.alter_column(
        "shorturl", "creation", existing_type=postgresql.TIMESTAMP(), nullable=False, schema=staticschema
    )
    # Add default value to nb_hits
    op.execute(f"UPDATE {staticschema}.shorturl SET nb_hits = 0 WHERE nb_hits IS NULL")
    op.alter_column("shorturl", "nb_hits", existing_type=sa.INTEGER(), nullable=False, schema=staticschema)
    # Add default value to is_password_changed and deactivated
    op.execute(
        f'UPDATE {staticschema}."user" SET is_password_changed = false WHERE is_password_changed IS NULL'
    )
    op.alter_column(
        "user", "is_password_changed", existing_type=sa.BOOLEAN(), nullable=False, schema=staticschema
    )
    op.execute(f'UPDATE {staticschema}."user" SET deactivated = false WHERE deactivated IS NULL')
    op.alter_column("user", "deactivated", existing_type=sa.BOOLEAN(), nullable=False, schema=staticschema)


def downgrade() -> None:
    """Downgrade."""
    staticschema = config["schema_static"]

    op.alter_column("user", "deactivated", existing_type=sa.BOOLEAN(), nullable=True, schema=staticschema)
    op.alter_column(
        "user", "is_password_changed", existing_type=sa.BOOLEAN(), nullable=True, schema=staticschema
    )
    op.alter_column("shorturl", "nb_hits", existing_type=sa.INTEGER(), nullable=True, schema=staticschema)
    op.alter_column(
        "shorturl", "creation", existing_type=postgresql.TIMESTAMP(), nullable=True, schema=staticschema
    )
    op.alter_column("shorturl", "url", existing_type=sa.VARCHAR(), nullable=True, schema=staticschema)
    op.alter_column(
        "oauth2_client", "pkce_required", existing_type=sa.BOOLEAN(), nullable=True, schema=staticschema
    )
    op.alter_column(
        "oauth2_client", "state_required", existing_type=sa.BOOLEAN(), nullable=True, schema=staticschema
    )
    op.alter_column(
        "oauth2_client", "redirect_uri", existing_type=sa.VARCHAR(), nullable=True, schema=staticschema
    )
    op.alter_column("oauth2_client", "secret", existing_type=sa.VARCHAR(), nullable=True, schema=staticschema)
    op.alter_column(
        "oauth2_client", "client_id", existing_type=sa.VARCHAR(), nullable=True, schema=staticschema
    )
    op.alter_column(
        "oauth2_bearertoken",
        "expire_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_bearertoken",
        "refresh_token",
        existing_type=sa.VARCHAR(length=100),
        nullable=True,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_bearertoken",
        "access_token",
        existing_type=sa.VARCHAR(length=100),
        nullable=True,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_authorizationcode",
        "expire_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        nullable=True,
        schema=staticschema,
    )
    op.alter_column(
        "oauth2_authorizationcode",
        "redirect_uri",
        existing_type=sa.VARCHAR(),
        nullable=True,
        schema=staticschema,
    )
