# -*- coding: utf-8 -*-

# Copyright (c) 2015-2019, Camptocamp SA
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

"""Add theme to FullTextSearch

Revision ID: 53ba1a68d5fe
Revises: 5109242131ce
Create Date: 2015-08-05 14:43:30.889188
"""

from alembic import op
from sqlalchemy import Column, Integer, ForeignKey, Boolean, String
from c2cgeoportal_commons.config import config

# revision identifiers, used by Alembic.
revision = '53ba1a68d5fe'
down_revision = '5109242131ce'


def upgrade():
    schema = config['schema']

    op.add_column('tsearch', Column(
        'interface_id', Integer,
        ForeignKey(schema + '.interface.id'),
        nullable=True
    ), schema=schema)
    op.add_column('tsearch', Column('lang', String(2), nullable=True), schema=schema)
    op.add_column('tsearch', Column('actions', String, nullable=True), schema=schema)
    op.add_column('tsearch', Column('from_theme', Boolean, server_default='false'), schema=schema)

    op.create_index(
        'tsearch_search_index',
        table_name='tsearch',
        columns=['ts', 'public', 'role_id', 'interface_id', 'lang'],
        schema=schema
    )


def downgrade():
    schema = config['schema']

    op.drop_index('tsearch_search_index', schema=schema)

    op.drop_column('tsearch', 'interface_id', schema=schema)
    op.drop_column('tsearch', 'lang', schema=schema)
    op.drop_column('tsearch', 'actions', schema=schema)
    op.drop_column('tsearch', 'from_theme', schema=schema)
