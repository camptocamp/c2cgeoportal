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

"""Cascade deletes to tsearch

Revision ID: e85afd327ab3
Revises: c75124553bf3
Create Date: 2019-03-28 11:52:48.520780
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = 'e85afd327ab3'
down_revision = 'c75124553bf3'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    op.drop_constraint('tsearch_role_id_fkey', 'tsearch', schema=schema, type_='foreignkey')
    op.create_foreign_key('tsearch_role_id_fkey', 'tsearch', 'role', ['role_id'], ['id'],
                          source_schema=schema, referent_schema=schema, ondelete='CASCADE')

    op.drop_constraint('tsearch_interface_id_fkey', 'tsearch', schema=schema, type_='foreignkey')
    op.create_foreign_key('tsearch_interface_id_fkey', 'tsearch', 'interface', ['interface_id'], ['id'],
                          source_schema=schema, referent_schema=schema, ondelete='CASCADE')


def downgrade():
    schema = config['schema']

    op.drop_constraint('tsearch_role_id_fkey', 'tsearch', schema=schema, type_='foreignkey')
    op.create_foreign_key('tsearch_role_id_fkey', 'tsearch', 'role', ['role_id'], ['id'],
                          source_schema=schema, referent_schema=schema)

    op.drop_constraint('tsearch_interface_id_fkey', 'tsearch', schema=schema, type_='foreignkey')
    op.create_foreign_key('tsearch_interface_id_fkey', 'tsearch', 'interface', ['interface_id'], ['id'],
                          source_schema=schema, referent_schema=schema)
