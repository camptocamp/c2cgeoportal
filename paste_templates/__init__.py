# -*- coding: utf-8 -*-

from paste.script import templates


class TemplateCreate(templates.Template):
    _template_dir = 'create'
    summary = 'Template used to create a c2cgeoportal project'
    vars = [
        templates.var('srid', 'A Spatial Reference System Identifier (e.g. 21781)'),
        templates.var(
            'version_table_suffix',
            'The sqlalchemy-migrate version table name suffix (this table ' \
                'will be named: "version_${package}${version_table_suffix}")'),
        ]

class TemplateUpdate(templates.Template):
    _template_dir = 'update'
    summary = 'Template used to update a c2cgeoportal project'

