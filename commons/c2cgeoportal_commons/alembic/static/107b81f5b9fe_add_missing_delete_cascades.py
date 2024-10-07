# Copyright (c) 2020-2024, Camptocamp SA
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
Add missing delete cascades.

Revision ID: 107b81f5b9fe
Revises: bd029dbfc11a
Create Date: 2020-05-25 15:13:12.194192
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "107b81f5b9fe"
down_revision = "bd029dbfc11a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    staticschema = config["schema_static"]

    op.drop_constraint("user_role_user_id_fkey", "user_role", schema=staticschema, type_="foreignkey")
    op.create_foreign_key(
        "user_role_user_id_fkey",
        "user_role",
        "user",
        ["user_id"],
        ["id"],
        source_schema=staticschema,
        referent_schema=staticschema,
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade."""
    staticschema = config["schema_static"]

    op.drop_constraint("user_role_user_id_fkey", "user_role", schema=staticschema, type_="foreignkey")
    op.create_foreign_key(
        "user_role_user_id_fkey",
        "user_role",
        "user",
        ["user_id"],
        ["id"],
        source_schema=staticschema,
        referent_schema=staticschema,
    )
