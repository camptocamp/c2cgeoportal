# -*- coding: utf-8 -*-

# Copyright (c) 2017-2019, Camptocamp SA
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

"""Be able to delete a linked functionality

Revision ID: d8ef99bc227e
Revises: 9268a1dffac0
Create Date: 2017-09-20 14:49:22.465328
"""

from alembic import op
import psycopg2
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = 'd8ef99bc227e'
down_revision = '9268a1dffac0'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    for source, dest in [
        ('role_functionality', 'role'),
        ('role_functionality', 'functionality'),
        ('theme_functionality', 'theme'),
        ('theme_functionality', 'functionality'),
    ]:
        try:
            op.drop_constraint('{}_{}_id_fkey'.format(source, dest), source, schema=schema)
        except psycopg2.ProgrammingError as e:
            print(e)
            print("The constraint will probably don't exists, so we continue.")

        op.create_foreign_key(
            '{}_{}_id_fkey'.format(source, dest),
            source, source_schema=schema, local_cols=['{}_id'.format(dest)],
            referent_table=dest, referent_schema=schema, remote_cols=['id'],
            ondelete='cascade',
        )


def downgrade():
    schema = config['schema']

    for source, dest in [
        ('role_functionality', 'role'),
        ('role_functionality', 'functionality'),
        ('theme_functionality', 'theme'),
        ('theme_functionality', 'functionality'),
    ]:
        op.drop_constraint('{}_{}_id_fkey'.format(source, dest), source, schema=schema)
        op.create_foreign_key(
            '{}_{}_id_fkey'.format(source, dest),
            source, source_schema=schema, local_cols=['{}_id'.format(dest)],
            referent_table=dest, referent_schema=schema, remote_cols=['id'],
        )
