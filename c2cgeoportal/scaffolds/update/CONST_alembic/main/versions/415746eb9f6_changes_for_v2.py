# -*- coding: utf-8 -*-

# Copyright (c) 2014-2016, Camptocamp SA
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

"""Changes to start the implementation of the version 2

Revision ID: 415746eb9f6
Revises: None
Create Date: 2014-10-23 16:00:47.940216
"""

from alembic import op, context
from sqlalchemy import Column, ForeignKey, Table, MetaData
from sqlalchemy.types import Integer, Boolean, Unicode, Float

# revision identifiers, used by Alembic.
revision = '415746eb9f6'
down_revision = '166ff2dcc48d'


def upgrade():
    schema = context.get_context().config.get_main_option('schema')

    engine = op.get_bind().engine
    if type(engine).__name__ != 'MockConnection' and \
            op.get_context().dialect.has_table(
                engine, 'interface', schema=schema):  # pragma: nocover
        return

    op.drop_table('user_functionality', schema=schema)

    op.create_table(
        'interface',
        Column(
            'id', Integer, primary_key=True
        ),
        Column('name', Unicode),
        Column('description', Unicode),
        schema=schema,
    )

    op.create_table(
        'interface_layer',
        Column(
            'interface_id', Integer, ForeignKey(schema + '.interface.id'), primary_key=True
        ),
        Column(
            'layer_id', Integer, ForeignKey(schema + '.layer.id'), primary_key=True
        ),
        schema=schema,
    )

    op.create_table(
        'interface_theme',
        Column(
            'interface_id', Integer, ForeignKey(schema + '.interface.id'), primary_key=True
        ),
        Column(
            'theme_id', Integer, ForeignKey(schema + '.theme.id'), primary_key=True
        ),
        schema=schema,
    )

    op.create_table(
        'layerv1',
        Column(
            'id', Integer, ForeignKey(schema + '.layer.id'), primary_key=True
        ),
        Column('is_checked', Boolean, default=True),
        Column('icon', Unicode),
        Column('layer_type', Unicode(12)),
        Column('url', Unicode),
        Column('image_type', Unicode(10)),
        Column('style', Unicode),
        Column('dimensions', Unicode),
        Column('matrix_set', Unicode),
        Column('wms_url', Unicode),
        Column('wms_layers', Unicode),
        Column('query_layers', Unicode),
        Column('kml', Unicode),
        Column('is_single_tile', Boolean),
        Column('legend', Boolean, default=True),
        Column('legend_image', Unicode),
        Column('legend_rule', Unicode),
        Column('is_legend_expanded', Boolean, default=False),
        Column('min_resolution', Float),
        Column('max_resolution', Float),
        Column('disclaimer', Unicode),
        Column('identifier_attribute_field', Unicode),
        Column('exclude_properties', Unicode),
        Column('time_mode', Unicode(8)),
        schema=schema,
    )

    op.execute(
        "UPDATE ONLY %(schema)s.treeitem SET type = 'layerv1' "
        "WHERE type='layer'" % {'schema': schema}
    )

    op.execute(
        'INSERT INTO %(schema)s.layerv1 ('
        'id, is_checked, icon, layer_type, url, image_type, style, dimensions, matrix_set, '
        'wms_url, wms_layers, query_layers, kml, is_single_tile, legend, '
        'legend_image, legend_rule, is_legend_expanded, min_resolution, max_resolution, '
        'disclaimer, identifier_attribute_field, exclude_properties, time_mode) '
        '(SELECT '
        'id, "isChecked" AS is_checked, icon, "layerType" AS layer_type, url, '
        '"imageType" AS image_type, style, dimensions, "matrixSet" AS matrix_set, '
        '"wmsUrl" AS wms_url, "wmsLayers" AS wms_layers, "queryLayers" AS query_layers, kml, '
        '"isSingleTile" AS is_single_tile, legend, "legendImage" AS legend_image, '
        '"legendRule" AS legend_rule, "isLegendExpanded" AS is_legend_expanded, '
        '"minResolution" AS min_resolution, "maxResolution" AS max_resolution, disclaimer, '
        '"identifierAttributeField" AS identifier_attribute_field, '
        '"excludeProperties" AS exclude_properties, "timeMode" AS time_mode '
        'FROM %(schema)s.layer)' % {'schema': schema}
    )

    op.drop_column('layer', 'isChecked', schema=schema)
    op.drop_column('layer', 'icon', schema=schema)
    op.drop_column('layer', 'layerType', schema=schema)
    op.drop_column('layer', 'url', schema=schema)
    op.drop_column('layer', 'imageType', schema=schema)
    op.drop_column('layer', 'style', schema=schema)
    op.drop_column('layer', 'dimensions', schema=schema)
    op.drop_column('layer', 'matrixSet', schema=schema)
    op.drop_column('layer', 'wmsUrl', schema=schema)
    op.drop_column('layer', 'wmsLayers', schema=schema)
    op.drop_column('layer', 'queryLayers', schema=schema)
    op.drop_column('layer', 'kml', schema=schema)
    op.drop_column('layer', 'isSingleTile', schema=schema)
    op.drop_column('layer', 'legend', schema=schema)
    op.drop_column('layer', 'legendImage', schema=schema)
    op.drop_column('layer', 'legendRule', schema=schema)
    op.drop_column('layer', 'isLegendExpanded', schema=schema)
    op.drop_column('layer', 'minResolution', schema=schema)
    op.drop_column('layer', 'maxResolution', schema=schema)
    op.drop_column('layer', 'disclaimer', schema=schema)
    op.drop_column('layer', 'identifierAttributeField', schema=schema)
    op.drop_column('layer', 'excludeProperties', schema=schema)
    op.drop_column('layer', 'timeMode', schema=schema)

    interface = Table(
        'interface', MetaData(),
        Column('name', Unicode),
        schema=schema,
    )
    op.bulk_insert(interface, [
        {'name': 'main'},
        {'name': 'mobile'},
        {'name': 'edit'},
        {'name': 'routing'},
    ])

    op.execute(
        'INSERT INTO %(schema)s.interface_layer (layer_id, interface_id) '
        '(SELECT l.id AS layer_id, i.id AS interface_id '
        'FROM %(schema)s.layer AS l, %(schema)s.interface AS i '
        'WHERE i.name in (\'main\', \'edit\', \'routing\') AND l."inDesktopViewer")' % {
            'schema': schema
        }
    )
    op.execute(
        'INSERT INTO %(schema)s.interface_layer (layer_id, interface_id) '
        '(SELECT l.id AS layer_id, i.id AS interface_id '
        'FROM %(schema)s.layer AS l, %(schema)s.interface AS i '
        'WHERE i.name = \'mobile\' AND l."inMobileViewer")' % {'schema': schema}
    )

    op.execute(
        'INSERT INTO %(schema)s.interface_theme (theme_id, interface_id) '
        '(SELECT l.id AS theme_id, i.id AS interface_id '
        'FROM %(schema)s.theme AS l, %(schema)s.interface AS i '
        'WHERE i.name in (\'main\', \'edit\', \'routing\') AND l."inDesktopViewer")' % {
            'schema': schema
        }
    )
    op.execute(
        'INSERT INTO %(schema)s.interface_theme (theme_id, interface_id) '
        '(SELECT l.id AS theme_id, i.id AS interface_id '
        'FROM %(schema)s.theme AS l, %(schema)s.interface AS i '
        'WHERE i.name = \'mobile\' AND l."inMobileViewer")' % {'schema': schema}
    )

    op.drop_column('layer', 'inMobileViewer', schema=schema)
    op.drop_column('layer', 'inDesktopViewer', schema=schema)

    op.alter_column('layer', 'geoTable', new_column_name='geo_table', schema=schema)

    op.drop_column('theme', 'inMobileViewer', schema=schema)
    op.drop_column('theme', 'inDesktopViewer', schema=schema)

    op.alter_column('treeitem', 'metadataURL', new_column_name='metadata_url', schema=schema)
    op.alter_column('layergroup', 'isExpanded', new_column_name='is_expanded', schema=schema)
    op.alter_column('layergroup', 'isInternalWMS', new_column_name='is_internal_wms', schema=schema)
    op.alter_column('layergroup', 'isBaseLayer', new_column_name='is_base_layer', schema=schema)

    op.create_table(
        'layer_internal_wms',
        Column(
            'id', Integer, ForeignKey(schema + '.layer.id'), primary_key=True
        ),
        Column('layer', Unicode),
        Column('image_type', Unicode(10)),
        Column('style', Unicode),
        Column('time_mode', Unicode(8)),
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
        schema=schema,
    )

    op.create_table(
        'layer_wmts',
        Column(
            'id', Integer, ForeignKey(schema + '.layer.id'), primary_key=True,
        ),
        Column('url', Unicode),
        Column('layer', Unicode),
        Column('style', Unicode),
        Column('matrix_set', Unicode),
        schema=schema,
    )

    op.create_table(
        'ui_metadata',
        Column(
            'id', Integer, primary_key=True
        ),
        Column('name', Unicode),
        Column('value', Unicode),
        Column('description', Unicode),
        Column('item_id', Integer, ForeignKey(schema + '.treeitem.id'), nullable=False),
        schema=schema,
    )

    op.create_table(
        'wmts_dimension',
        Column(
            'id', Integer, primary_key=True
        ),
        Column('name', Unicode),
        Column('value', Unicode),
        Column('description', Unicode),
        Column('layer_id', Integer, ForeignKey(schema + '.layer_wmts.id'), nullable=False),
        schema=schema,
    )


def downgrade():
    schema = context.get_context().config.get_main_option('schema')

    op.drop_table('wmts_dimension', schema=schema)
    op.drop_table('ui_metadata', schema=schema)
    op.drop_table('layer_wmts', schema=schema)
    op.drop_table('layer_external_wms', schema=schema)
    op.drop_table('layer_internal_wms', schema=schema)

    op.add_column('layer', Column('inMobileViewer', Boolean, default=False), schema=schema)
    op.add_column('layer', Column('inDesktopViewer', Boolean, default=True), schema=schema)

    op.alter_column('layer', 'geo_table', new_column_name='geoTable', schema=schema)

    op.add_column('theme', Column('inMobileViewer', Boolean, default=False), schema=schema)
    op.add_column('theme', Column('inDesktopViewer', Boolean, default=True), schema=schema)

    op.alter_column('treeitem', 'metadata_url', new_column_name='metadataURL', schema=schema)
    op.alter_column('layergroup', 'is_expanded', new_column_name='isExpanded', schema=schema)
    op.alter_column('layergroup', 'is_internal_wms', new_column_name='isInternalWMS', schema=schema)
    op.alter_column('layergroup', 'is_base_layer', new_column_name='isBaseLayer', schema=schema)

    op.execute(
        'UPDATE ONLY %(schema)s.theme AS t '
        'SET "inDesktopViewer" = FALSE' % {'schema': schema}
    )
    op.execute(
        'UPDATE ONLY %(schema)s.layer AS t '
        'SET "inDesktopViewer" = FALSE' % {'schema': schema}
    )

    op.execute(
        'UPDATE ONLY %(schema)s.theme AS t '
        'SET "inMobileViewer" = TRUE '
        'FROM %(schema)s.interface AS i, %(schema)s.interface_theme AS it '
        'WHERE i.name = \'mobile\' AND i.id = it.interface_id AND it.theme_id = t.id' % {
            'schema': schema
        }
    )
    op.execute(
        'UPDATE ONLY %(schema)s.theme AS t '
        'SET "inDesktopViewer" = TRUE '
        'FROM %(schema)s.interface AS i, %(schema)s.interface_theme AS it '
        'WHERE i.name = \'main\' AND i.id = it.interface_id AND it.theme_id = t.id' % {
            'schema': schema
        }
    )
    op.execute(
        'UPDATE ONLY %(schema)s.layer AS l '
        'SET "inMobileViewer" = TRUE '
        'FROM %(schema)s.interface AS i, %(schema)s.interface_layer AS il '
        'WHERE i.name = \'mobile\' AND i.id = il.interface_id AND il.layer_id = l.id' % {
            'schema': schema
        }
    )
    op.execute(
        'UPDATE ONLY %(schema)s.layer AS l '
        'SET "inDesktopViewer" = TRUE '
        'FROM %(schema)s.interface AS i, %(schema)s.interface_layer AS il '
        'WHERE i.name = \'main\' AND i.id = il.interface_id AND il.layer_id = l.id' % {
            'schema': schema
        }
    )

    op.add_column('layer', Column('timeMode', Unicode(8)), schema=schema)
    op.add_column('layer', Column('excludeProperties', Unicode), schema=schema)
    op.add_column('layer', Column('identifierAttributeField', Unicode), schema=schema)
    op.add_column('layer', Column('disclaimer', Unicode), schema=schema)
    op.add_column('layer', Column('maxResolution', Float), schema=schema)
    op.add_column('layer', Column('minResolution', Float), schema=schema)
    op.add_column('layer', Column('isLegendExpanded', Boolean, default=False), schema=schema)
    op.add_column('layer', Column('legendRule', Unicode), schema=schema)
    op.add_column('layer', Column('legendImage', Unicode), schema=schema)
    op.add_column('layer', Column('legend', Boolean, default=True), schema=schema)
    op.add_column('layer', Column('isSingleTile', Boolean, default=False), schema=schema)
    op.add_column('layer', Column('kml', Unicode), schema=schema)
    op.add_column('layer', Column('queryLayers', Unicode), schema=schema)
    op.add_column('layer', Column('wmsLayers', Unicode), schema=schema)
    op.add_column('layer', Column('wmsUrl', Unicode), schema=schema)
    op.add_column('layer', Column('matrixSet', Unicode), schema=schema)
    op.add_column('layer', Column('dimensions', Unicode), schema=schema)
    op.add_column('layer', Column('style', Unicode), schema=schema)
    op.add_column('layer', Column('imageType', Unicode(10)), schema=schema)
    op.add_column('layer', Column('url', Unicode), schema=schema)
    op.add_column('layer', Column('layerType', Unicode(12)), schema=schema)
    op.add_column('layer', Column('icon', Unicode), schema=schema)
    op.add_column('layer', Column('isChecked', Boolean, default=True), schema=schema)

    op.execute(
        'UPDATE %(schema)s.layer AS l SET ('
        'id, "isChecked", icon, "layerType", url, "imageType", style, dimensions, "matrixSet", '
        '"wmsUrl", "wmsLayers", "queryLayers", kml, "isSingleTile", legend, "legendImage", '
        '"legendRule", "isLegendExpanded", "minResolution", "maxResolution", disclaimer, '
        '"identifierAttributeField", "excludeProperties", "timeMode"'
        ') = ('
        'o.id, o.is_checked, o.icon, o.layer_type, o.url, o.image_type, o.style, o.dimensions, '
        'o.matrix_set, o.wms_url, o.wms_layers, o.query_layers, o.kml, o.is_single_tile, '
        'o.legend, o.legend_image, o.legend_rule, o.is_legend_expanded, o.min_resolution, '
        'o.max_resolution, o.disclaimer, o.identifier_attribute_field, o.exclude_properties, '
        'o.time_mode '
        ') FROM %(schema)s.layerv1 AS o WHERE o.id = l.id' % {'schema': schema}
    )

    op.drop_table('layerv1', schema=schema)
    op.drop_table('interface_theme', schema=schema)
    op.drop_table('interface_layer', schema=schema)
    op.drop_table('interface', schema=schema)

    op.create_table(
        'user_functionality',
        Column(
            'user_id', Integer,
            ForeignKey(schema + '.user.id'), primary_key=True
        ),
        Column(
            'functionality_id', Integer,
            ForeignKey(schema + '.functionality.id'), primary_key=True
        ),
        schema=schema,
    )
