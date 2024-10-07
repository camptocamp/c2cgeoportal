# Copyright (c) 2015-2024, Camptocamp SA
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

# pylint: disable=no-member,invalid-name

"""
Add description column in the tree.

Revision ID: 22e6dfb556de
Revises: 2b8ed8c1df94
Create Date: 2015-12-04 13:44:42.475652
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column, Unicode

# revision identifiers, used by Alembic.
revision = "22e6dfb556de"
down_revision = "2b8ed8c1df94"


def upgrade() -> None:
    """Upgrade."""
    schema = config["schema"]

    # Instructions
    op.add_column("layergroup_treeitem", Column("description", Unicode), schema=schema)
    op.add_column("treeitem", Column("description", Unicode), schema=schema)


def downgrade() -> None:
    """Downgrade."""
    schema = config["schema"]

    # Instructions
    op.drop_column("layergroup_treeitem", "description", schema=schema)
    op.drop_column("treeitem", "description", schema=schema)
