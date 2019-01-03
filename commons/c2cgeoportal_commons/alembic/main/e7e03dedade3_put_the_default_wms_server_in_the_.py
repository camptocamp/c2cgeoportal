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

"""Put the default WMS server in the servers part, add some constrains

Revision ID: e7e03dedade3
Revises: daf738d5bae4
Create Date: 2016-08-26 14:39:21.984921
"""

from alembic import op
from c2cgeoportal_commons.config import config

# revision identifiers, used by Alembic.
revision = 'e7e03dedade3'
down_revision = '8117bb9bba16'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    op.execute("""
        UPDATE "{schema}".ogc_server
        SET url = 'config://local/mapserv'
        WHERE url IS NULL
    """.format(schema=schema))

    op.alter_column('ogc_server', 'url', nullable=False, schema=schema)
    op.create_unique_constraint('name_unique_ogc_server', 'ogc_server', ['name'], schema=schema)
    op.alter_column('treeitem', 'name', nullable=False, schema=schema)
    op.create_unique_constraint(
        'type_name_unique_treeitem', 'treeitem', ['type', 'name'], schema=schema
    )


def downgrade():
    schema = config['schema']

    op.alter_column('ogc_server', 'url', nullable=True, schema=schema)
    op.drop_constraint('name_unique_ogc_server', 'ogc_server', schema=schema)
    op.alter_column('treeitem', 'name', nullable=True, schema=schema)
    op.drop_constraint('type_name_unique_treeitem', 'treeitem', schema=schema)

    op.execute("""
        UPDATE "{schema}".ogc_server
        SET url = NULL
        WHERE url = 'config://local/mapserv'
    """.format(schema=schema))
