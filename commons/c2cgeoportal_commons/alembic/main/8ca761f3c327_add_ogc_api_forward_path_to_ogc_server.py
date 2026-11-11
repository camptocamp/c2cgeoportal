# Copyright (c) 2026, Camptocamp SA
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
Add OGC API forward path to OGC server.

Revision ID: 8ca761f3c327
Revises: 33528a10237c
Create Date: 2026-11-11 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "8ca761f3c327"
down_revision = "33528a10237c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    schema = config["schema"]

    op.add_column(
        "ogc_server",
        sa.Column(
            "ogc_api_forward_path",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        schema=schema,
    )
    # QGIS Server builds the OGC API links from the request URL path, enable the forwarding
    # of the full client visible path for the existing QGIS Server OGC servers.
    op.execute(f"UPDATE {schema}.ogc_server SET ogc_api_forward_path = TRUE WHERE type = 'qgisserver'")


def downgrade() -> None:
    """Downgrade."""
    schema = config["schema"]

    op.drop_column("ogc_server", "ogc_api_forward_path", schema=schema)
