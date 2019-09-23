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

"""Add API's intrfaces

Revision ID: 78fd093c8393
Revises: e85afd327ab3
Create Date: 2019-08-29 07:56:15.547216
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, MetaData, Table
from sqlalchemy.types import Unicode

# revision identifiers, used by Alembic.
revision = '78fd093c8393'
down_revision = 'e85afd327ab3'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    # Instructions
    interface = Table(
        'interface', MetaData(),
        Column('name', Unicode),
        schema=schema,
    )
    connection = op.get_bind()
    for interface_name in ('api', 'iframe_api'):
        results = connection.execute("SELECT name FROM {schema}.interface WHERE name='{name}'".format(
            name=interface_name, schema=schema
        ))
        if not results:
            op.bulk_insert(interface, [
                {'name': interface_name},
            ])
    for interface_name in ('edit', 'routing'):
        results = connection.execute("SELECT name FROM {schema}.interface WHERE name='{name}'".format(
            name=interface_name, schema=schema
        ))
        if results:
            op.execute(
                "DELETE FROM {schema}.interface_theme it "
                "USING {schema}.interface i "
                "WHERE it.interface_id = i.id AND i.name = '{name}'".format(
                    name=interface_name, schema=schema
                )
            )
            op.execute(
                "DELETE FROM {schema}.interface_layer il "
                "USING {schema}.interface i "
                "WHERE il.interface_id = i.id AND i.name = '{name}'".format(
                    name=interface_name, schema=schema
                )
            )
            op.execute("DELETE FROM {schema}.interface WHERE name='{name}'".format(
                name=interface_name, schema=schema
            ))


def downgrade():
    schema = config['schema']

    # Instructions
    interface = Table(
        'interface', MetaData(),
        Column('name', Unicode),
        schema=schema,
    )
    connection = op.get_bind()
    for interface_name in ('edit', 'routing'):
        results = connection.execute("SELECT name FROM {schema}.interface WHERE name='{name}'".format(
            name=interface_name, schema=schema
        ))
        if not results:
            op.bulk_insert(interface, [
                {'name': interface_name},
            ])
    for interface_name in ('api', 'iframe_api'):
        results = connection.execute("SELECT name FROM {schema}.interface WHERE name='{name}'".format(
            name=interface_name, schema=schema
        ))
        if results:
            op.execute(
                "DELETE FROM {schema}.interface_theme it "
                "USING {schema}.interface i "
                "WHERE it.interface_id = i.id AND i.name = '{name}'".format(
                    name=interface_name, schema=schema
                )
            )
            op.execute(
                "DELETE FROM {schema}.interface_layer il "
                "USING {schema}.interface i "
                "WHERE il.interface_id = i.id AND i.name = '{name}'".format(
                    name=interface_name, schema=schema
                )
            )
            op.execute("DELETE FROM {schema}.interface WHERE name='{name}'".format(
                name=interface_name, schema=schema
            ))
