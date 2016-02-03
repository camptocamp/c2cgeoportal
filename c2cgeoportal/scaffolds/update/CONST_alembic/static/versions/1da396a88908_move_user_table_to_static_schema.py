
# Copyright (c) 2015-2016, Camptocamp SA
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


"""Move user table to static schema

Revision ID: 1da396a88908
Revises: 3f89a7d71a5e
Create Date: 2015-02-20 14:09:04.875390
"""

from alembic import op, context
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Unicode, Boolean

# revision identifiers, used by Alembic.
revision = '1da396a88908'
down_revision = '3f89a7d71a5e'


def upgrade():
    schema = context.get_context().config.get_main_option('schema')
    staticschema = schema + '_static'
    parentschema = context.get_context().config.get_main_option('parentschema')

    engine = op.get_bind().engine
    if type(engine).__name__ != 'MockConnection' and \
            op.get_context().dialect.has_table(
                engine, 'user', schema=staticschema):  # pragma: nocover
        return

    op.create_table(
        'user',
        Column('type', String(10), nullable=False),
        Column('id', Integer, primary_key=True),
        Column('username', Unicode, unique=True, nullable=False),
        Column('password', Unicode, nullable=False),
        Column('email', Unicode, nullable=False),
        Column('is_password_changed', Boolean, default=False),
        Column('role_name', String),
        schema=staticschema,
    )
    parent_column = ''
    parent_select = ''
    parent_join = ''
    if parentschema is not None and parentschema is not '':  # pragma: nocover
        op.add_column(
            'user',
            Column('parent_role_name', String),
            schema=staticschema
        )
        parent_column = ', parent_role_name'
        parent_select = ', pr.name'
        parent_join = (
            'LEFT OUTER JOIN %(parentschema)s.role AS pr ON (pr.id = u.parent_role_id)' % {
                'parentschema': parentschema,
            }
        )

    op.execute(
        'INSERT INTO %(staticschema)s.user '
        '(type, username, password, email, is_password_changed, role_name%(parent_column)s) ('
        'SELECT u.type, u.username, u.password, u.email, '
        'u.is_password_changed, r.name%(parent_select)s '
        'FROM %(schema)s.user AS u '
        'LEFT OUTER JOIN %(schema)s.role AS r ON (r.id = u.role_id) %(parent_join)s'
        ')' % {
            'staticschema': staticschema,
            'schema': schema,
            'parent_select': parent_select,
            'parent_column': parent_column,
            'parent_join': parent_join,
        }
    )

    op.drop_table('user', schema=schema)


def downgrade():
    schema = context.get_context().config.get_main_option('schema')
    staticschema = schema + '_static'
    parentschema = context.get_context().config.get_main_option('parentschema')

    op.create_table(
        'user',
        Column('type', String(10), nullable=False),
        Column('id', Integer, primary_key=True),
        Column('username', Unicode, unique=True, nullable=False),
        Column('password', Unicode, nullable=False),
        Column('email', Unicode, nullable=False),
        Column('is_password_changed', Boolean, default=False),
        Column('role_id', Integer, ForeignKey(schema + '.role.id'), nullable=False),
        schema=schema,
    )
    parent_column = ''
    parent_select = ''
    parent_join = ''
    if parentschema is not None and parentschema is not '':  # pragma: nocover
        op.add_column(
            'user',
            Column('parent_role_id', Integer, ForeignKey(parentschema + '.role.id')),
            schema=schema
        )
        parent_column = ', parent_role_id'
        parent_select = ', pr.id'
        parent_join = (
            'LEFT OUTER JOIN %(parentschema)s.role AS pr ON (pr.name = u.parent_role_name)' % {
                'parentschema': parentschema,
            }
        )

    op.execute(
        'INSERT INTO %(schema)s.user '
        '(type, username, password, email, is_password_changed, role_id%(parent_column)s) ('
        'SELECT u.type, u.username, u.password, u.email, '
        'u.is_password_changed, r.id%(parent_select)s '
        'FROM %(staticschema)s.user AS u '
        'LEFT OUTER JOIN %(schema)s.role AS r ON (r.name = u.role_name) %(parent_join)s'
        ')' % {
            'staticschema': staticschema,
            'schema': schema,
            'parent_select': parent_select,
            'parent_column': parent_column,
            'parent_join': parent_join,
        }
    )

    op.drop_table('user', schema=staticschema)
