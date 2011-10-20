# -*- coding: utf-8 -*-

from paste.script import templates

vars = [
    templates.var('srid', 'A Spatial Reference System Identifier (e.g. 21781)'),
    ]

class TemplateCreate(templates.Template):
    _template_dir = 'create'
    summary = 'Template used to create a c2cgeoportal project'
    vars = vars

class TemplateUpdate(templates.Template):
    _template_dir = 'update'
    summary = 'Template used to update a c2cgeoportal project'
    vars = vars

