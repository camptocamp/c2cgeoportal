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

"""Add vector tiles layers table

Revision ID: 678f88c7ad5e
Revises: 028477929d13
Create Date: 2019-09-27 13:51:08.255601
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, ForeignKey, Integer, Unicode

# revision identifiers, used by Alembic.
revision = "678f88c7ad5e"
down_revision = "028477929d13"
branch_labels = None
depends_on = None


def upgrade():
    schema = config["schema"]

    op.create_table(
        "layer_vectortiles",
        Column("id", Integer, ForeignKey(schema + ".layer.id"), primary_key=True),
        Column("style", Unicode, nullable=False),
        Column("xyz", Unicode, nullable=True),
        schema=schema,
    )


def downgrade():
    schema = config["schema"]

    op.drop_table("layer_vectortiles", schema=schema)
