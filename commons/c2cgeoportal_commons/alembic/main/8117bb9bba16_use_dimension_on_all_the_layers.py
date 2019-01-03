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

"""Use dimension on all the layers

Revision ID: 8117bb9bba16
Revises: daf738d5bae4
Create Date: 2016-08-16 16:53:07.012668
"""

from alembic import op
from c2cgeoportal_commons.config import config

# revision identifiers, used by Alembic.
revision = '8117bb9bba16'
down_revision = 'b60f2a505f42'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    op.rename_table('wmts_dimension', 'dimension', schema=schema)
    with op.batch_alter_table('dimension', schema=schema) as table_op:
        table_op.drop_constraint('wmts_dimension_layer_id_fkey', type_='foreignkey')
        table_op.create_foreign_key(
            'dimension_layer_id_fkey', local_cols=['layer_id'],
            referent_schema=schema, referent_table='layer', remote_cols=['id'],
        )


def downgrade():
    schema = config['schema']

    with op.batch_alter_table('dimension', schema=schema) as table_op:
        table_op.drop_constraint('dimension_layer_id_fkey', type_='foreignkey')
        table_op.create_foreign_key(
            'wmts_dimension_layer_id_fkey', local_cols=['layer_id'],
            referent_schema=schema, referent_table='layer_wmts', remote_cols=['id'],
        )
    op.rename_table('dimension', 'wmts_dimension', schema=schema)
