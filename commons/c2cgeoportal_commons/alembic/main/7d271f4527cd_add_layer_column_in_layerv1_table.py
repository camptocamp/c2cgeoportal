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

"""Add layer column in layerv1 table

Revision ID: 7d271f4527cd
Revises: 8117bb9bba16
Create Date: 2016-10-20 15:00:13.619090
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column
from sqlalchemy.types import Unicode

# revision identifiers, used by Alembic.
revision = "7d271f4527cd"
down_revision = "8117bb9bba16"
branch_labels = None
depends_on = None


def upgrade():
    schema = config["schema"]

    op.add_column("layerv1", Column("layer", Unicode), schema=schema)
    op.execute(
        "UPDATE {schema}.layerv1 AS l1 "
        "SET layer = name "
        "FROM {schema}.treeitem AS ti "
        "WHERE l1.id = ti.id".format(schema=schema)
    )


def downgrade():
    schema = config["schema"]

    op.drop_column("layerv1", "layer", schema=schema)
