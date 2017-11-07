# -*- coding: utf-8 -*-

# Copyright (c) 2015-2017, Camptocamp SA
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

"""Set layergroup_treeitem.id as a primary key

Revision ID: 2b8ed8c1df94
Revises: 26a8c51827c6
Create Date: 2015-10-29 16:11:24.760733
"""

from alembic import op, context

# revision identifiers, used by Alembic.
revision = '2b8ed8c1df94'
down_revision = '32527659d57b'
branch_labels = None
depends_on = None


def upgrade():
    schema = context.get_context().config.get_main_option('schema')

    op.create_primary_key(
        'layergroup_treeitem_pkey', 'layergroup_treeitem', ['id'],
        schema=schema
    )


def downgrade():
    schema = context.get_context().config.get_main_option('schema')

    op.drop_constraint(
        'layergroup_treeitem_pkey', 'layergroup_treeitem', schema=schema
    )
