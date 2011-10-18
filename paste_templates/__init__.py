# -*- coding: utf-8 -*-

from paste.script.templates import Template

class TemplateCreate(Template):
    _template_dir = 'create'
    summary = 'Template used to create a c2cgeoportal project'
    vars = []

class TemplateUpdate(Template):
    _template_dir = 'update'
    summary = 'Template used to update a c2cgeoportal project'
    vars = []

