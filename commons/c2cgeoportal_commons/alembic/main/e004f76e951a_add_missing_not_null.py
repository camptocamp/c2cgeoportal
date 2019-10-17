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

"""Add missing not null

Revision ID: e004f76e951a
Revises: ee25d267bf46
Create Date: 2016-10-06 15:28:17.418830
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "e004f76e951a"
down_revision = "ee25d267bf46"
branch_labels = None
depends_on = None


def upgrade():
    schema = config["schema"]

    op.alter_column("layer_wmts", "url", nullable=False, schema=schema)
    op.alter_column("layer_wmts", "layer", nullable=False, schema=schema)
    op.execute(
        "UPDATE ONLY {schema}.layer_wmts SET image_type = 'image/png' where image_type IS NULL".format(
            schema=schema
        )
    )
    op.alter_column("layer_wmts", "image_type", nullable=False, schema=schema)
    op.alter_column("layer_wms", "ogc_server_id", nullable=False, schema=schema)
    op.alter_column("layer_wms", "layer", nullable=False, schema=schema)
    op.execute(
        "UPDATE ONLY {schema}.layer_wms SET time_mode = 'disabled' where time_mode IS NULL".format(
            schema=schema
        )
    )
    op.alter_column("layer_wms", "time_mode", nullable=False, schema=schema)
    op.execute(
        "UPDATE ONLY {schema}.layer_wms SET time_widget = 'slider' where time_widget IS NULL".format(
            schema=schema
        )
    )
    op.alter_column("layer_wms", "time_widget", nullable=False, schema=schema)
    op.execute(
        "UPDATE ONLY {schema}.ogc_server SET image_type = 'image/png' where image_type IS NULL".format(
            schema=schema
        )
    )
    op.alter_column("ogc_server", "image_type", nullable=False, schema=schema)
    op.execute(
        "UPDATE ONLY {schema}.ogc_server SET type = 'mapserver' where type IS NULL".format(schema=schema)
    )
    op.alter_column("ogc_server", "type", nullable=False, schema=schema)
    op.execute(
        "UPDATE ONLY {schema}.ogc_server SET auth = 'Standard auth' where auth IS NULL".format(schema=schema)
    )
    op.alter_column("ogc_server", "auth", nullable=False, schema=schema)


def downgrade():
    schema = config["schema"]

    op.alter_column("layer_wmts", "url", nullable=True, schema=schema)
    op.alter_column("layer_wmts", "layer", nullable=True, schema=schema)
    op.alter_column("layer_wmts", "image_type", nullable=True, schema=schema)
    op.alter_column("layer_wms", "ogc_server_id", nullable=True, schema=schema)
    op.alter_column("layer_wms", "layer", nullable=True, schema=schema)
    op.alter_column("layer_wms", "time_mode", nullable=True, schema=schema)
    op.alter_column("layer_wms", "time_widget", nullable=True, schema=schema)
    op.alter_column("ogc_server", "image_type", nullable=True, schema=schema)
    op.alter_column("ogc_server", "type", nullable=True, schema=schema)
    op.alter_column("ogc_server", "auth", nullable=True, schema=schema)
