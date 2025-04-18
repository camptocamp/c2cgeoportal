# Copyright (c) 2015-2025, Camptocamp SA
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
Move exclude_properties from LayerV1 to Layer.

Revision ID: 32527659d57b
Revises: 5109242131ce
Create Date: 2015-10-19 16:31:24.894791
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Column
from sqlalchemy.types import Unicode

# revision identifiers, used by Alembic.
revision = "32527659d57b"
down_revision = "5109242131ce"


def upgrade() -> None:
    """Upgrade."""
    schema = config["schema"]

    op.add_column("layer", Column("exclude_properties", Unicode), schema=schema)
    op.execute(
        f"UPDATE {schema}.layer as l1 SET exclude_properties = l2.exclude_properties "
        f"FROM {schema}.layerv1 as l2 "
        "WHERE l1.id = l2.id",
    )
    op.drop_column("layerv1", "exclude_properties", schema=schema)


def downgrade() -> None:
    """Downgrade."""
    schema = config["schema"]

    op.add_column("layerv1", Column("exclude_properties", Unicode), schema=schema)
    op.execute(
        f"UPDATE {schema}.layerv1 as l1 SET exclude_properties = l2.exclude_properties "
        f"FROM {schema}.layer as l2 "
        "WHERE l1.id = l2.id",
    )
    op.drop_column("layer", "exclude_properties", schema=schema)
