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

# pylint: disable=no-member,invalid-name

"""
Add missing delete cascades.

Revision ID: 87f8330ed64e
Revises: 16e43f8c0330
Create Date: 2020-05-25 14:53:36.289305
"""

import sqlalchemy as sa
from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "87f8330ed64e"
down_revision = "16e43f8c0330"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    schema = config["schema"]

    op.drop_constraint(
        "interface_layer_interface_id_fkey", "interface_layer", schema=schema, type_="foreignkey"
    )
    op.create_foreign_key(
        "interface_layer_interface_id_fkey",
        "interface_layer",
        "interface",
        ["interface_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "interface_theme_interface_id_fkey", "interface_theme", schema=schema, type_="foreignkey"
    )
    op.drop_constraint("interface_theme_theme_id_fkey", "interface_theme", schema=schema, type_="foreignkey")
    op.create_foreign_key(
        "interface_theme_interface_id_fkey",
        "interface_theme",
        "interface",
        ["interface_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "interface_theme_theme_id_fkey",
        "interface_theme",
        "theme",
        ["theme_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "layer_restrictionarea_restrictionarea_id_fkey",
        "layer_restrictionarea",
        schema=schema,
        type_="foreignkey",
    )
    op.drop_constraint(
        "layer_restrictionarea_layer_id_fkey", "layer_restrictionarea", schema=schema, type_="foreignkey"
    )
    op.create_foreign_key(
        "layer_restrictionarea_layer_id_fkey",
        "layer_restrictionarea",
        "layer",
        ["layer_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "layer_restrictionarea_restrictionarea_id_fkey",
        "layer_restrictionarea",
        "restrictionarea",
        ["restrictionarea_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "restricted_role_theme_theme_id_fkey", "restricted_role_theme", schema=schema, type_="foreignkey"
    )
    op.drop_constraint(
        "restricted_role_theme_role_id_fkey", "restricted_role_theme", schema=schema, type_="foreignkey"
    )
    op.create_foreign_key(
        "restricted_role_theme_theme_id_fkey",
        "restricted_role_theme",
        "theme",
        ["theme_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "restricted_role_theme_role_id_fkey",
        "restricted_role_theme",
        "role",
        ["role_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "role_restrictionarea_role_id_fkey", "role_restrictionarea", schema=schema, type_="foreignkey"
    )
    op.drop_constraint(
        "role_restrictionarea_restrictionarea_id_fkey",
        "role_restrictionarea",
        schema=schema,
        type_="foreignkey",
    )
    op.create_foreign_key(
        "role_restrictionarea_role_id_fkey",
        "role_restrictionarea",
        "role",
        ["role_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "role_restrictionarea_restrictionarea_id_fkey",
        "role_restrictionarea",
        "restrictionarea",
        ["restrictionarea_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
        ondelete="CASCADE",
    )

    op.alter_column("theme", "ordering", existing_type=sa.INTEGER(), nullable=False, schema=schema)


def downgrade() -> None:
    """Downgrade."""
    schema = config["schema"]

    op.alter_column("theme", "ordering", existing_type=sa.INTEGER(), nullable=True, schema=schema)

    op.drop_constraint(
        "role_restrictionarea_restrictionarea_id_fkey",
        "role_restrictionarea",
        schema=schema,
        type_="foreignkey",
    )
    op.drop_constraint(
        "role_restrictionarea_role_id_fkey", "role_restrictionarea", schema=schema, type_="foreignkey"
    )
    op.create_foreign_key(
        "role_restrictionarea_restrictionarea_id_fkey",
        "role_restrictionarea",
        "restrictionarea",
        ["restrictionarea_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )
    op.create_foreign_key(
        "role_restrictionarea_role_id_fkey",
        "role_restrictionarea",
        "role",
        ["role_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )

    op.drop_constraint(
        "restricted_role_theme_role_id_fkey", "restricted_role_theme", schema=schema, type_="foreignkey"
    )
    op.drop_constraint(
        "restricted_role_theme_theme_id_fkey", "restricted_role_theme", schema=schema, type_="foreignkey"
    )
    op.create_foreign_key(
        "restricted_role_theme_role_id_fkey",
        "restricted_role_theme",
        "role",
        ["role_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )
    op.create_foreign_key(
        "restricted_role_theme_theme_id_fkey",
        "restricted_role_theme",
        "theme",
        ["theme_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )

    op.alter_column("ogc_server", "name", existing_type=sa.VARCHAR(), nullable=False, schema=schema)

    op.drop_constraint(
        "layer_restrictionarea_layer_id_fkey", "layer_restrictionarea", schema=schema, type_="foreignkey"
    )
    op.drop_constraint(
        "layer_restrictionarea_restrictionarea_id_fkey",
        "layer_restrictionarea",
        schema=schema,
        type_="foreignkey",
    )
    op.create_foreign_key(
        "layer_restrictionarea_layer_id_fkey",
        "layer_restrictionarea",
        "layer",
        ["layer_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )
    op.create_foreign_key(
        "layer_restrictionarea_restrictionarea_id_fkey",
        "layer_restrictionarea",
        "restrictionarea",
        ["restrictionarea_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )

    op.drop_constraint("interface_theme_theme_id_fkey", "interface_theme", schema=schema, type_="foreignkey")
    op.drop_constraint(
        "interface_theme_interface_id_fkey", "interface_theme", schema=schema, type_="foreignkey"
    )
    op.create_foreign_key(
        "interface_theme_theme_id_fkey",
        "interface_theme",
        "theme",
        ["theme_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )
    op.create_foreign_key(
        "interface_theme_interface_id_fkey",
        "interface_theme",
        "interface",
        ["interface_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )

    op.drop_constraint(
        "interface_layer_interface_id_fkey", "interface_layer", schema=schema, type_="foreignkey"
    )
    op.create_foreign_key(
        "interface_layer_interface_id_fkey",
        "interface_layer",
        "interface",
        ["interface_id"],
        ["id"],
        source_schema=schema,
        referent_schema=schema,
    )
