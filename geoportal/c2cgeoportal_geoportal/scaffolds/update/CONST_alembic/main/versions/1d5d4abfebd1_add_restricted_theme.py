# Copyright (c) 2014-2017, Camptocamp SA
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

"""Add restricted theme

Revision ID: 1d5d4abfebd1
Revises: 54645a535ad6
Create Date: 2014-11-25 16:51:51.567026
"""

from alembic import op, context
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, Boolean

# revision identifiers, used by Alembic.
revision = '1d5d4abfebd1'
down_revision = '54645a535ad6'


def upgrade():
    schema = context.get_context().config.get_main_option('schema')

    engine = op.get_bind().engine
    if type(engine).__name__ != 'MockConnection' and \
            op.get_context().dialect.has_table(
                engine, 'restricted_role_theme', schema=schema):  # pragma: no cover
        return

    op.add_column('theme', Column(
        'public', Boolean, server_default='t', nullable=False
    ), schema=schema)
    op.create_table(
        'restricted_role_theme',
        Column(
            'role_id', Integer, ForeignKey(schema + '.role.id'), primary_key=True
        ),
        Column(
            'theme_id', Integer, ForeignKey(schema + '.theme.id'), primary_key=True
        ),
        schema=schema
    )


def downgrade():
    schema = context.get_context().config.get_main_option('schema')

    op.drop_table('restricted_role_theme', schema=schema)
    op.drop_column('theme', 'public', schema=schema)
