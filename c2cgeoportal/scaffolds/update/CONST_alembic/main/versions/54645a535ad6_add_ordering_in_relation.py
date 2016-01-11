# -*- coding: utf-8 -*-

# Copyright (c) 2014-2016, Camptocamp SA
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

"""Add ordering in relation

Revision ID: 54645a535ad6
Revises: 415746eb9f6
Create Date: 2014-11-25 14:39:05.110315
"""

from alembic import op, context
from sqlalchemy import Column
from sqlalchemy.types import Integer

# revision identifiers, used by Alembic.
revision = '54645a535ad6'
down_revision = '415746eb9f6'


def upgrade():
    schema = context.get_context().config.get_main_option('schema')

    op.drop_constraint('layergroup_treeitem_pkey', 'layergroup_treeitem', schema=schema)
    op.add_column('layergroup_treeitem', Column('id', Integer, primary_key=True), schema=schema)
    op.add_column('layergroup_treeitem', Column('ordering', Integer), schema=schema)
    op.execute(
        'UPDATE ONLY %(schema)s.layergroup_treeitem AS lt SET ordering = ti."order" '
        'FROM %(schema)s.treeitem AS ti WHERE ti.id = lt.treeitem_id ' % {'schema': schema}
    )
    op.add_column('theme', Column('ordering', Integer), schema=schema)
    op.execute(
        'UPDATE ONLY %(schema)s.theme AS t SET ordering = ti."order" '
        'FROM %(schema)s.treeitem AS ti WHERE ti.id = t.id ' % {'schema': schema}
    )
    op.drop_column('treeitem', 'order', schema=schema)


def downgrade():
    schema = context.get_context().config.get_main_option('schema')
    op.add_column('treeitem', Column('order', Integer), schema=schema)
    op.execute(
        'UPDATE ONLY %(schema)s.treeitem AS ti SET "order" = lt.ordering '
        'FROM %(schema)s.layergroup_treeitem AS lt WHERE ti.id = lt.treeitem_id ' % {
            'schema': schema
        }
    )
    op.execute(
        'UPDATE ONLY %(schema)s.treeitem AS ti SET "order" = t.ordering '
        'FROM %(schema)s.theme AS t WHERE ti.id = t.id ' % {'schema': schema}
    )
    op.drop_column('theme', 'ordering', schema=schema)
    op.drop_column('layergroup_treeitem', 'ordering', schema=schema)
    op.drop_column('layergroup_treeitem', 'id', schema=schema)
    op.create_primary_key(
        'layergroup_treeitem_pkey', 'layergroup_treeitem',
        ['treegroup_id', 'treeitem_id'], schema=schema
    )
