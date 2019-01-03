# -*- coding: utf-8 -*-

# Copyright (c) 2015-2019, Camptocamp SA
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

"""internal and external layer tables refactoring, new ogc table

Revision ID: 116b9b79fc4d
Revises: 1418cb05921b
Create Date: 2015-10-28 12:21:59.162238
"""

from alembic import op
from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Boolean, Unicode
from c2cgeoportal_commons.config import config

# revision identifiers, used by Alembic.
revision = '116b9b79fc4d'
down_revision = 'a4f1aac9bda'
branch_labels = None
depends_on = None


def upgrade():
    schema = config['schema']

    # Instructions
    op.create_table(
        'server_ogc',
        Column('id', Integer, primary_key=True),
        Column('name', Unicode, nullable=False),
        Column('description', Unicode),
        Column('url', Unicode),
        # url_wfs needed for Arcgis because wms and wfs url may be different
        Column('url_wfs', Unicode),
        Column('type', Unicode),
        Column('image_type', Unicode),
        Column('auth', Unicode),
        Column('wfs_support', Boolean, server_default='false'),
        Column('is_single_tile', Boolean, server_default='false'),
        schema=schema,
    )

    op.create_table(
        'layer_wms',
        Column(
            'id', Integer,
            ForeignKey(schema + '.layer.id'), primary_key=True
        ),
        Column(
            'server_ogc_id', Integer,
            ForeignKey(schema + '.server_ogc.id')
        ),
        Column('layer', Unicode),
        Column('style', Unicode),
        Column('time_mode', Unicode, server_default='disabled', nullable=False),
        Column('time_widget', Unicode, server_default='slider', nullable=False),
        schema=schema,
    )

    # move data from layer_internal_wms and layer_external_wms to the new
    # layer_wms and server_ogc tables

    # ocg for internal

    # default 'image/jpeg', 'image/png'
    op.execute(
        'INSERT INTO %(schema)s.server_ogc (name, description, type, image_type, '
        "  auth, wfs_support) "
        "SELECT 'source for ' || image_type AS name, "
        "  'default source for internal ' || image_type AS description, "
        "  'mapserver' AS type, "
        "  image_type, "
        "  'Standard auth' AS auth, "
        "  'true' AS wfs_support "
        "FROM ("
        "  SELECT UNNEST(ARRAY['image/jpeg', 'image/png']) AS image_type"
        ") AS foo" % {
            'schema': schema,
        }
    )
    # other custom image types
    op.execute(
        'INSERT INTO %(schema)s.server_ogc (name, description, type, image_type, '
        "  auth, wfs_support) "
        "SELECT 'source for ' || image_type AS name, "
        "  'default source for internal ' || image_type AS description, "
        "  'mapserver' AS type, "
        "  image_type, "
        "  'Standard auth' AS auth, "
        "  'true' AS wfs_support "
        "FROM ("
        "  SELECT DISTINCT(image_type) FROM %(schema)s.layer_internal_wms "
        "  WHERE image_type NOT IN ('image/jpeg', 'image/png')"
        ") as foo" % {
            'schema': schema,
        }
    )

    # layers for internal

    # internal with not null image_type
    op.execute(
        'INSERT INTO %(schema)s.layer_wms (id, server_ogc_id, layer, style, '
        '  time_mode, time_widget) '
        'SELECT lew.id, so.id, layer, style, time_mode, time_widget '
        'FROM %(schema)s.layer_internal_wms AS lew, %(schema)s.server_ogc AS so '
        'WHERE lew.image_type=so.image_type AND so.type IS NOT NULL' % {
            'schema': schema,
        }
    )
    # internal with null image_type
    op.execute(
        'INSERT INTO %(schema)s.layer_wms (id, server_ogc_id, layer, style, '
        '  time_mode, time_widget) '
        'SELECT lew.id, so.id, layer, style, time_mode, time_widget '
        'FROM %(schema)s.layer_internal_wms AS lew, %(schema)s.server_ogc AS so '
        "WHERE lew.image_type IS NULL AND so.image_type='image/png'" % {
            'schema': schema,
        }
    )

    # ocg for externals
    op.execute(
        'INSERT INTO %(schema)s.server_ogc (name, url, type, image_type, auth, is_single_tile) '
        "SELECT 'source for ' || url, url, 'mapserver' AS type, image_type, 'none', CASE "
        'WHEN is_single_tile IS TRUE THEN TRUE ELSE FALSE END as is_single_tile '
        'FROM %(schema)s.layer_external_wms GROUP BY url, image_type, is_single_tile' % {
            'schema': schema,
        }
    )

    # layers for external
    op.execute(
        'INSERT INTO %(schema)s.layer_wms (id, server_ogc_id, layer, style, '
        '  time_mode, time_widget) '
        'SELECT lew.id, so.id, layer, style, time_mode, time_widget '
        'FROM %(schema)s.layer_external_wms as lew, %(schema)s.server_ogc as so '
        'WHERE lew.url=so.url AND lew.is_single_tile=so.is_single_tile '
        'AND lew.image_type=so.image_type' % {
            'schema': schema,
        }
    )

    op.drop_table('layer_external_wms', schema=schema)
    op.drop_table('layer_internal_wms', schema=schema)

    # update layer type in treeitems
    op.execute(
        'UPDATE %(schema)s.treeitem '
        "SET type='l_wms' "
        "WHERE type='l_int_wms' OR type='l_ext_wms'" % {
            'schema': schema,
        }
    )


def downgrade():
    schema = config['schema']

    # Instructions

    # recreate tables 'layer_internal_wms' and 'layer_external_wms'
    op.create_table(
        'layer_internal_wms',
        Column(
            'id', Integer, ForeignKey(schema + '.layer.id'), primary_key=True
        ),
        Column('layer', Unicode),
        Column('image_type', Unicode(10)),
        Column('style', Unicode),
        Column('time_mode', Unicode(8)),
        Column('time_widget', Unicode(10), server_default='slider'),
        schema=schema,
    )

    op.create_table(
        'layer_external_wms',
        Column(
            'id', Integer, ForeignKey(schema + '.layer.id'), primary_key=True
        ),
        Column('url', Unicode),
        Column('layer', Unicode),
        Column('image_type', Unicode(10)),
        Column('style', Unicode),
        Column('is_single_tile', Boolean),
        Column('time_mode', Unicode(8)),
        Column('time_widget', Unicode(10), server_default='slider'),
        schema=schema,
    )
    # move data back

    # internal (type is not null)
    op.execute(
        'INSERT INTO %(schema)s.layer_internal_wms (id, layer, image_type, style, '
        '  time_mode, time_widget) '
        'SELECT w.id, layer, image_type, style, time_mode, time_widget '
        'FROM %(schema)s.layer_wms AS w, %(schema)s.server_ogc AS o '
        'WHERE w.server_ogc_id=o.id AND o.type IS NOT NULL' % {
            'schema': schema,
        }
    )

    # external (type is null)
    op.execute(
        'INSERT INTO %(schema)s.layer_external_wms (id, url, layer, image_type, style, '
        '  is_single_tile, time_mode, time_widget) '
        'SELECT w.id, url, layer, image_type, style, is_single_tile, time_mode, time_widget '
        'FROM %(schema)s.layer_wms AS w, %(schema)s.server_ogc AS o '
        'WHERE w.server_ogc_id=o.id AND o.type IS NULL' % {
            'schema': schema,
        }
    )

    # drop table AFTER moving data back
    op.drop_table('layer_wms', schema=schema)
    op.drop_table('server_ogc', schema=schema)

    # update layer type in treeitems
    # internal
    op.execute(
        "UPDATE %(schema)s.treeitem "
        "SET type='l_int_wms' "
        "FROM %(schema)s.layer_internal_wms as w "
        "WHERE %(schema)s.treeitem.id=w.id" % {
            'schema': schema,
        }
    )
    # external
    op.execute(
        "UPDATE %(schema)s.treeitem "
        "SET type='l_ext_wms' "
        "FROM %(schema)s.layer_external_wms as w "
        "WHERE %(schema)s.treeitem.id=w.id" % {
            'schema': schema,
        }
    )
