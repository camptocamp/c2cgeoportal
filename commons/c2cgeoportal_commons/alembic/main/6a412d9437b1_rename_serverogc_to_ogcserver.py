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

"""Rename ServerOGC to OGCServer

Revision ID: 6a412d9437b1
Revises: 29f2a32859ec
Create Date: 2016-06-28 18:08:23.888198
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "6a412d9437b1"
down_revision = "29f2a32859ec"
branch_labels = None
depends_on = None


def upgrade():
    schema = config["schema"]

    op.rename_table("server_ogc", "ogc_server", schema=schema)
    with op.batch_alter_table("layer_wms", schema=schema) as table_op:
        table_op.alter_column("server_ogc_id", new_column_name="ogc_server_id")


def downgrade():
    schema = config["schema"]

    op.rename_table("ogc_server", "server_ogc", schema=schema)
    with op.batch_alter_table("layer_wms", schema=schema) as table_op:
        table_op.alter_column("ogc_server_id", new_column_name="server_ogc_id")
