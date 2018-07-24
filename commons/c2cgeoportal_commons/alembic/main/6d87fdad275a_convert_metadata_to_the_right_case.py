# -*- coding: utf-8 -*-

# Copyright (c) 2017, Camptocamp SA
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

"""Convert the metadata to the right case

Revision ID: 6d87fdad275a
Revises: 9268a1dffac0
Create Date: 2017-09-05 11:18:52.494205
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = '6d87fdad275a'
down_revision = '9268a1dffac0'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    op.execute(
        "UPDATE ONLY {schema}.metadata SET name = 'copyTo' where name = 'copy_to'"
        .format(schema=schema)
    )
    op.execute(
        "UPDATE ONLY {schema}.metadata SET name = 'geometryValidation' where name = 'geometry_validation'"
        .format(schema=schema)
    )


def downgrade():
    schema = config['schema']

    op.execute(
        "UPDATE ONLY {schema}.metadata SET name = 'copy_to' where name = 'copyTo'"
        .format(schema=schema)
    )
    op.execute(
        "UPDATE ONLY {schema}.metadata SET name = 'geometry_validation' where name = 'geometryValidation'"
        .format(schema=schema)
    )
