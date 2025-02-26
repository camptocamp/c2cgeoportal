# Copyright (c) 2024-2025, Camptocamp SA
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

Revision ID: b6b09f414fe8
Revises: 44c91d82d419
Create Date: 2024-04-22 07:17:25.399062
"""

import sqlalchemy as sa
from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "b6b09f414fe8"
down_revision = "44c91d82d419"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    schema = config["schema"]

    # names are required
    op.alter_column("dimension", "name", existing_type=sa.VARCHAR(), nullable=False, schema=schema)
    op.alter_column("interface", "name", existing_type=sa.VARCHAR(), nullable=False, schema=schema)
    op.alter_column("restrictionarea", "name", existing_type=sa.VARCHAR(), nullable=False, schema=schema)
    # Set a default value to boolean ind int
    op.execute(f"UPDATE {schema}.layer SET public = true WHERE public IS NULL")
    op.alter_column("layer", "public", existing_type=sa.BOOLEAN(), nullable=False, schema=schema)
    op.execute(f"UPDATE {schema}.layergroup_treeitem SET ordering = 0 WHERE ordering IS NULL")
    op.alter_column(
        "layergroup_treeitem", "ordering", existing_type=sa.INTEGER(), nullable=False, schema=schema
    )
    op.alter_column("metadata", "name", existing_type=sa.VARCHAR(), nullable=False, schema=schema)
    op.execute(f"UPDATE {schema}.ogc_server SET wfs_support = false WHERE wfs_support IS NULL")
    op.alter_column(
        "ogc_server",
        "wfs_support",
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default="false",
        schema=schema,
    )
    op.execute(f"UPDATE {schema}.ogc_server SET is_single_tile = false WHERE is_single_tile IS NULL")
    op.alter_column(
        "ogc_server",
        "is_single_tile",
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default="false",
        schema=schema,
    )
    op.execute(f"UPDATE {schema}.restrictionarea SET readwrite = false WHERE readwrite IS NULL")
    op.alter_column("restrictionarea", "readwrite", existing_type=sa.BOOLEAN(), nullable=False, schema=schema)
    # Add missing index
    # Remove it if he al ready exists
    connection = op.get_bind()
    if op.get_context().dialect.has_index(
        connection,
        index_name="idx_restrictionarea_area",
        table_name="restrictionarea",
        schema=schema,
    ):
        op.drop_index(
            "idx_restrictionarea_area", table_name="restrictionarea", schema=schema, postgresql_using="gist"
        )

    op.create_index(
        "idx_restrictionarea_area",
        "restrictionarea",
        ["area"],
        unique=False,
        schema=schema,
        postgresql_using="gist",
    )
    # label is required
    op.alter_column("tsearch", "label", existing_type=sa.VARCHAR(), nullable=False, schema=schema)
    # Add default value
    op.execute(f"UPDATE {schema}.tsearch SET public = true WHERE public IS NULL")
    op.alter_column(
        "tsearch",
        "public",
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default="true",
        schema=schema,
    )
    op.execute(f"UPDATE {schema}.tsearch SET from_theme = false WHERE from_theme IS NULL")
    op.alter_column(
        "tsearch",
        "from_theme",
        existing_type=sa.BOOLEAN(),
        nullable=False,
        existing_server_default="false",
        schema=schema,
    )


def downgrade() -> None:
    """Downgrade."""
    schema = config["schema"]

    op.alter_column(
        "tsearch",
        "from_theme",
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default="false",
        schema=schema,
    )
    op.alter_column(
        "tsearch",
        "public",
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default="true",
        schema=schema,
    )
    op.alter_column("tsearch", "label", existing_type=sa.VARCHAR(), nullable=True, schema=schema)
    op.alter_column("restrictionarea", "readwrite", existing_type=sa.BOOLEAN(), nullable=True, schema=schema)
    op.alter_column("restrictionarea", "name", existing_type=sa.VARCHAR(), nullable=True, schema=schema)
    op.alter_column(
        "ogc_server",
        "is_single_tile",
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default="false",
        schema=schema,
    )
    op.alter_column(
        "ogc_server",
        "wfs_support",
        existing_type=sa.BOOLEAN(),
        nullable=True,
        existing_server_default="false",
        schema=schema,
    )
    op.alter_column("metadata", "name", existing_type=sa.VARCHAR(), nullable=True, schema=schema)
    op.alter_column(
        "layergroup_treeitem", "ordering", existing_type=sa.INTEGER(), nullable=True, schema=schema
    )
    op.alter_column("layer", "public", existing_type=sa.BOOLEAN(), nullable=True, schema=schema)
    op.alter_column("interface", "name", existing_type=sa.VARCHAR(), nullable=True, schema=schema)
    op.alter_column("dimension", "name", existing_type=sa.VARCHAR(), nullable=True, schema=schema)
