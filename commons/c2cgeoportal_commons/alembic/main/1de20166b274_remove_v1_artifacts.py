# -*- coding: utf-8 -*-

# Copyright (c) 2019, Camptocamp SA
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

"""Remove v1 artifacts

Revision ID: 1de20166b274
Revises: e85afd327ab3
Create Date: 2019-05-01 12:09:04.929610
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Boolean, Float, Integer, Unicode

# revision identifiers, used by Alembic.
revision = "1de20166b274"
down_revision = "e85afd327ab3"
branch_labels = None
depends_on = None


def upgrade():
    schema = config["schema"]

    op.drop_table("layerv1", schema=schema)


def downgrade():
    schema = config["schema"]

    op.create_table(
        "layerv1",
        Column("id", Integer, ForeignKey(schema + ".layer.id", ondelete="cascade"), primary_key=True),
        Column("is_checked", Boolean, default=True),
        Column("icon", Unicode),
        Column("layer_type", Unicode(12)),
        Column("url", Unicode),
        Column("image_type", Unicode(10)),
        Column("style", Unicode),
        Column("dimensions", Unicode),
        Column("matrix_set", Unicode),
        Column("wms_url", Unicode),
        Column("wms_layers", Unicode),
        Column("query_layers", Unicode),
        Column("kml", Unicode),
        Column("is_single_tile", Boolean),
        Column("legend", Boolean, default=True),
        Column("legend_image", Unicode),
        Column("legend_rule", Unicode),
        Column("is_legend_expanded", Boolean, default=False),
        Column("min_resolution", Float),
        Column("max_resolution", Float),
        Column("disclaimer", Unicode),
        Column("identifier_attribute_field", Unicode),
        Column("time_mode", Unicode(8)),
        Column("time_widget", Unicode(10), default="slider"),
        Column("layer", Unicode),
        schema=schema,
    )
