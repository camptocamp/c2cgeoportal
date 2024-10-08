# Copyright (c) 2014-2024, Camptocamp SA
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
Update icons url.

Revision ID: 20137477bd02
Revises: 415746eb9f6
Create Date: 2014-12-10 17:50:36.176587
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "20137477bd02"
down_revision = "1d5d4abfebd1"


def upgrade() -> None:
    """Upgrade."""
    schema = config["schema"]

    updates = [
        "UPDATE %(schema)s.%(table)s SET %(column)s = 'static:///' || %(column)s "
        "WHERE (%(column)s IS NOT NULL) AND (NOT %(column)s = '') "
        "AND NOT (%(column)s LIKE 'http%%') "
        "AND NOT (%(column)s LIKE '/%%')",
        "UPDATE %(schema)s.%(table)s SET %(column)s = 'static://' || %(column)s "
        "WHERE (%(column)s IS NOT NULL) AND (NOT %(column)s = '') "
        "AND NOT (%(column)s LIKE 'http%%') AND NOT (%(column)s LIKE 'static://%%')",
    ]
    for update in updates:
        op.execute(update % {"schema": schema, "table": "theme", "column": "icon"})
        op.execute(update % {"schema": schema, "table": "layerv1", "column": "icon"})
        op.execute(update % {"schema": schema, "table": "layerv1", "column": "kml"})
        op.execute(update % {"schema": schema, "table": "layerv1", "column": "legend_image"})


def downgrade() -> None:
    """Downgrade."""
    schema = config["schema"]

    updates = [
        "UPDATE %(schema)s.%(table)s SET %(column)s = substring(%(column)s from 11) "
        "WHERE %(column)s LIKE 'static:///%%'",
        "UPDATE %(schema)s.%(table)s SET %(column)s = substring(%(column)s from 10) "
        "WHERE %(column)s LIKE 'static://%%'",
    ]
    for update in updates:
        op.execute(update % {"schema": schema, "table": "theme", "column": "icon"})
        op.execute(update % {"schema": schema, "table": "layerv1", "column": "icon"})
        op.execute(update % {"schema": schema, "table": "layerv1", "column": "kml"})
        op.execute(update % {"schema": schema, "table": "layerv1", "column": "legend_image"})
