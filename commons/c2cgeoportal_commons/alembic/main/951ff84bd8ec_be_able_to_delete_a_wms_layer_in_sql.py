# -*- coding: utf-8 -*-

# Copyright (c) 2016-2019, Camptocamp SA
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

"""Be able to delete a WMS layer in SQL

Revision ID: 951ff84bd8ec
Revises: 29f2a32859ec
Create Date: 2016-06-22 15:29:24.210097
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "951ff84bd8ec"
down_revision = "29f2a32859ec"
branch_labels = None
depends_on = None


def upgrade():
    schema = config["schema"]

    op.drop_constraint("layergroup_treeitem_treeitem_id_fkey", "layergroup_treeitem", schema=schema)
    op.create_foreign_key(
        "layergroup_treeitem_treeitem_id_fkey",
        "layergroup_treeitem",
        source_schema=schema,
        local_cols=["treeitem_id"],
        referent_table="treeitem",
        referent_schema=schema,
        remote_cols=["id"],
        ondelete="cascade",
    )

    op.drop_constraint("treegroup_id_fkey", "treegroup", schema=schema)
    op.create_foreign_key(
        "treegroup_id_fkey",
        "treegroup",
        source_schema=schema,
        local_cols=["id"],
        referent_table="treeitem",
        referent_schema=schema,
        remote_cols=["id"],
        ondelete="cascade",
    )

    op.drop_constraint("ui_metadata_item_id_fkey", "ui_metadata", schema=schema)
    op.create_foreign_key(
        "ui_metadata_item_id_fkey",
        "ui_metadata",
        source_schema=schema,
        local_cols=["item_id"],
        referent_table="treeitem",
        referent_schema=schema,
        remote_cols=["id"],
        ondelete="cascade",
    )

    op.drop_constraint("layer_id_fkey", "layer", schema=schema)
    op.create_foreign_key(
        "layer_id_fkey",
        "layer",
        source_schema=schema,
        local_cols=["id"],
        referent_table="treeitem",
        referent_schema=schema,
        remote_cols=["id"],
        ondelete="cascade",
    )

    op.drop_constraint("layergroup_id_fkey", "layergroup", schema=schema)
    op.create_foreign_key(
        "layergroup_id_fkey",
        "layergroup",
        source_schema=schema,
        local_cols=["id"],
        referent_table="treegroup",
        referent_schema=schema,
        remote_cols=["id"],
        ondelete="cascade",
    )

    op.drop_constraint("interface_layer_layer_id_fkey", "interface_layer", schema=schema)
    op.create_foreign_key(
        "interface_layer_layer_id_fkey",
        "interface_layer",
        source_schema=schema,
        local_cols=["layer_id"],
        referent_table="layer",
        referent_schema=schema,
        remote_cols=["id"],
        ondelete="cascade",
    )

    op.drop_constraint("layer_wms_id_fkey", "layer_wms", schema=schema)
    op.create_foreign_key(
        "layer_wms_id_fkey",
        "layer_wms",
        source_schema=schema,
        local_cols=["id"],
        referent_table="layer",
        referent_schema=schema,
        remote_cols=["id"],
        ondelete="cascade",
    )


def downgrade():
    schema = config["schema"]

    op.drop_constraint("layergroup_treeitem_treeitem_id_fkey", "layergroup_treeitem", schema=schema)
    op.create_foreign_key(
        "layergroup_treeitem_treeitem_id_fkey",
        "layergroup_treeitem",
        source_schema=schema,
        local_cols=["treeitem_id"],
        referent_table="treeitem",
        referent_schema=schema,
        remote_cols=["id"],
    )

    op.drop_constraint("treegroup_id_fkey", "treegroup", schema=schema)
    op.create_foreign_key(
        "treegroup_id_fkey",
        "treegroup",
        source_schema=schema,
        local_cols=["id"],
        referent_table="treeitem",
        referent_schema=schema,
        remote_cols=["id"],
    )

    op.drop_constraint("ui_metadata_item_id_fkey", "ui_metadata", schema=schema)
    op.create_foreign_key(
        "ui_metadata_item_id_fkey",
        "ui_metadata",
        source_schema=schema,
        local_cols=["item_id"],
        referent_table="treeitem",
        referent_schema=schema,
        remote_cols=["id"],
    )

    op.drop_constraint("layer_id_fkey", "layer", schema=schema)
    op.create_foreign_key(
        "layer_id_fkey",
        "layer",
        source_schema=schema,
        local_cols=["id"],
        referent_table="treeitem",
        referent_schema=schema,
        remote_cols=["id"],
    )

    op.drop_constraint("layergroup_id_fkey", "layergroup", schema=schema)
    op.create_foreign_key(
        "layergroup_id_fkey",
        "layergroup",
        source_schema=schema,
        local_cols=["id"],
        referent_table="treegroup",
        referent_schema=schema,
        remote_cols=["id"],
    )

    op.drop_constraint("interface_layer_layer_id_fkey", "interface_layer", schema=schema)
    op.create_foreign_key(
        "interface_layer_layer_id_fkey",
        "interface_layer",
        source_schema=schema,
        local_cols=["layer_id"],
        referent_table="layer",
        referent_schema=schema,
        remote_cols=["id"],
    )

    op.drop_constraint("layer_wms_id_fkey", "layer_wms", schema=schema)
    op.create_foreign_key(
        "layer_wms_id_fkey",
        "layer_wms",
        source_schema=schema,
        local_cols=["id"],
        referent_table="layer",
        referent_schema=schema,
        remote_cols=["id"],
    )
