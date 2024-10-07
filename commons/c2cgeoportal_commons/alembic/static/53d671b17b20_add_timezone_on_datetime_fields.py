# Copyright (c) 2018-2024, Camptocamp SA
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
Add timezone on datetime fields.

Revision ID: 53d671b17b20
Revises: 1857owc78a07
Create Date: 2018-05-29 08:44:17.675988
"""

from alembic import op
from c2c.template.config import config

# revision identifiers, used by Alembic.
revision = "53d671b17b20"
down_revision = "1857owc78a07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade."""
    staticschema = config["schema_static"]

    op.execute(
        """
SET TIME ZONE 'UTC';
ALTER TABLE {staticschema}.user ALTER COLUMN last_login TYPE timestamp with time zone;
SET TIME ZONE LOCAL;
ALTER TABLE {staticschema}.user ALTER COLUMN expire_on TYPE timestamp with time zone;
""".format(
            staticschema=staticschema
        )
    )


def downgrade() -> None:
    """Downgrade."""
    staticschema = config["schema_static"]

    op.execute(
        """
SET TIME ZONE 'UTC';
ALTER TABLE {staticschema}.user ALTER COLUMN last_login TYPE timestamp without time zone;
SET TIME ZONE LOCAL;
ALTER TABLE {staticschema}.user ALTER COLUMN expire_on TYPE timestamp without time zone;
""".format(
            staticschema=staticschema
        )
    )
