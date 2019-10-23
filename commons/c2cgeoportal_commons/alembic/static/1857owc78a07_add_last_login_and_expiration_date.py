# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019, Camptocamp SA
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


"""
Add columns last_login, expire_on (both datetime) and deactivated (boolean) on
table main_static."user".

Revision ID: 1857owc78a07
Revises: 5472fbc19f39
Create Date: 2018-03-29 13:15:23.228907
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Boolean, Column, DateTime

# revision identifiers, used by Alembic.
revision = "1857owc78a07"
down_revision = "5472fbc19f39"


def upgrade():
    staticschema = config["schema_static"]

    # Instructions
    op.add_column("user", Column("last_login", DateTime), schema=staticschema)
    op.add_column("user", Column("expire_on", DateTime), schema=staticschema)
    op.add_column("user", Column("deactivated", Boolean, default=False), schema=staticschema)


def downgrade():
    staticschema = config["schema_static"]

    # Instructions
    op.drop_column("user", "deactivated", schema=staticschema)
    op.drop_column("user", "expire_on", schema=staticschema)
    op.drop_column("user", "last_login", schema=staticschema)
