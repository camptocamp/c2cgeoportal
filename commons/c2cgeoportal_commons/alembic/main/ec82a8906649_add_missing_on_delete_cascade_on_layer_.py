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

"""Add missing on delete cascade on layer tree

Revision ID: ec82a8906649
Revises: e7e03dedade3
Create Date: 2016-08-30 13:43:30.969505
"""

from alembic import op
from c2cgeoportal_commons.config import config

# revision identifiers, used by Alembic.
revision = 'ec82a8906649'
down_revision = 'e7e03dedade3'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    for source, dest in [
        ('layer_wmts', 'layer'),
        ('layerv1', 'layer'),
        ('theme', 'treegroup'),
    ]:
        op.drop_constraint(
            '{}_id_fkey'.format(source),
            source, schema=schema,
        )
        op.create_foreign_key(
            '{}_id_fkey'.format(source),
            source, source_schema=schema, local_cols=['id'],
            referent_table=dest, referent_schema=schema, remote_cols=['id'],
            ondelete='cascade',
        )


def downgrade():
    schema = config['schema']

    for source, dest in [
        ('layer_wmts', 'layer'),
        ('layerv1', 'layer'),
        ('theme', 'treegroup'),
    ]:
        op.drop_constraint(
            '{}_id_fkey'.format(source),
            source, schema=schema,
        )
        op.create_foreign_key(
            '{}_id_fkey'.format(source),
            source, source_schema=schema, local_cols=['id'],
            referent_table=dest, referent_schema=schema, remote_cols=['id'],
        )
