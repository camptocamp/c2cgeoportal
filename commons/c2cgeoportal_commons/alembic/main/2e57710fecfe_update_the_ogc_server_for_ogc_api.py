# Copyright (c) 2024-2025, Camptocamp SA
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
Update the OGC server for OGC API.

Revision ID: 2e57710fecfe
Revises: a4558f032d7d
Create Date: 2024-11-27 12:47:20.234376
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "2e57710fecfe"
down_revision = "a4558f032d7d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    schema = config["schema"]

    # Instructions

    # default 'image/jpeg', 'image/png'
    op.execute(f"UPDATE {schema}.ogc_server SET name = 'MapServer' WHERE name = 'source for image/png'")
    op.execute(f"UPDATE {schema}.ogc_server SET name = 'MapServer_JPEG' WHERE name = 'source for image/jpeg'")
    op.execute(
        f"UPDATE {schema}.ogc_server SET url = 'config://mapserver/mapserv_proxy/MapServer?MAP=MapServer' WHERE url = 'config://mapserver'"
    )
    op.execute(
        f"UPDATE {schema}.metadata SET value = 'MapServer' WHERE value = 'source for image/png' and name = 'ogcServer'"
    )


def downgrade() -> None:
    """Downgrade."""
    schema = config["schema"]

    # Instructions
    op.execute(f"UPDATE {schema}.ogc_server SET name = 'source for image/png' WHERE name = 'MapServer'")
    op.execute(f"UPDATE {schema}.ogc_server SET name = 'source for image/jpeg' WHERE name = 'MapServer_JPEG'")
    op.execute(
        f"UPDATE {schema}.ogc_server SET url = 'config://mapserver' WHERE url = 'config://mapserver/mapserv_proxy/MapServer?MAP=MapServer'"
    )
    op.execute(
        f"UPDATE {schema}.metadata SET value = 'source for image/png' WHERE value = 'MapServer' and name = 'ogcServer'"
    )
