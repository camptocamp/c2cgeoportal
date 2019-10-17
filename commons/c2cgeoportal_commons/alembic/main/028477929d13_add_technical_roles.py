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

"""Add technical roles

Revision ID: 028477929d13
Revises: eeb345672454
Create Date: 2019-10-04 09:33:30.363888
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, MetaData, Table
from sqlalchemy.types import Unicode

# revision identifiers, used by Alembic.
revision = "028477929d13"
down_revision = "eeb345672454"
branch_labels = None
depends_on = None


def upgrade():
    schema = config["schema"]

    role = Table("role", MetaData(), Column("name", Unicode), Column("description", Unicode), schema=schema)
    op.bulk_insert(
        role,
        [
            {"name": name, "description": description}
            for name, description in (
                ("anonymous", "Used to define default functionalities for all the users"),
                ("registered", "Used to define default functionalities for registered users"),
                ("intranet", "Used to define default functionalities for accesses from the intranet"),
            )
        ],
    )


def downgrade():
    schema = config["schema"]

    for name in ("anonymous", "registered", "intranet"):
        op.execute('DELETE FROM {schema}."role" ' "WHERE name = '{name}'".format(name=name, schema=schema))
