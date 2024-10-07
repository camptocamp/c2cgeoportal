# Copyright (c) 2023-2024, Camptocamp SA
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

# pylint: disable=invalid-name

"""
Add Oauth2 - PKCE.

Revision ID: 76d72fb3fcb9
Revises: 44c91d82d419
Create Date: 2023-02-07 17:32:22.835450
"""

from alembic import op
from c2c.template.config import config
from sqlalchemy import Boolean, Column, String

# revision identifiers, used by Alembic.
revision = "76d72fb3fcb9"
down_revision = "44c91d82d419"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    staticschema = config["schema_static"]

    op.add_column("oauth2_client", Column("state_required", Boolean), schema=staticschema)
    op.add_column("oauth2_client", Column("pkce_required", Boolean), schema=staticschema)
    op.add_column("oauth2_bearertoken", Column("state", String), schema=staticschema)
    op.add_column("oauth2_authorizationcode", Column("state", String), schema=staticschema)
    op.add_column("oauth2_authorizationcode", Column("challenge", String(128)), schema=staticschema)
    op.add_column("oauth2_authorizationcode", Column("challenge_method", String(6)), schema=staticschema)


def downgrade() -> None:
    """Downgrade."""
    staticschema = config["schema_static"]

    op.drop_column("oauth2_client", "state_required", schema=staticschema)
    op.drop_column("oauth2_client", "pkce_required", schema=staticschema)
    op.drop_column("oauth2_bearertoken", "state", schema=staticschema)
    op.drop_column("oauth2_authorizationcode", "state", schema=staticschema)
    op.drop_column("oauth2_authorizationcode", "challenge", schema=staticschema)
    op.drop_column("oauth2_authorizationcode", "challenge_method", schema=staticschema)
