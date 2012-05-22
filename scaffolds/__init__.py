# -*- coding: utf-8 -*-

import re

from pyramid.scaffolds.template import Template
from pyramid.compat import input_


class BaseTemplate(Template):
    """
    A class that can be used as a base class for c2cgeoportal scaffolding
    templates.

    Greatly inspired from ``pyramid.scaffolds.template.PyramidTemplate``.
    """

    def pre(self, command, output_dir, vars):
        """
        Overrides ``pyramid.scaffold.template.Template.pre``, adding
        several variables to the default variables list. Also prevents
        common misnamings (such as naming a package "site" or naming a
        package logger "root").
        """

        ret = Template.pre(self, command, output_dir, vars)

        self._set_package_in_vars(command, vars)

        if vars['package'] == 'site':
            raise ValueError(
                'Sorry, you may not name your package "site". '
                'The package name "site" has a special meaning in '
                'Python.  Please name it anything except "site".')

        package_logger = vars['package']
        if package_logger == 'root':
            # Rename the app logger in the rare case a project
            # is named 'root'
            package_logger = 'app'
        vars['package_logger'] = package_logger

        return ret

    def _set_package_in_vars(self, command, vars):
        """
        Set the package into the vars dict.
        """
        for arg in command.args:
            m = re.match('package=(\w+)', arg)
            if m:
                vars['package'] = m.group(1)
                break

    def out(self, msg):  # pragma: no cover (replaceable testing hook)
        print(msg)


class TemplateCreate(BaseTemplate):
    _template_dir = 'create'
    summary = 'Template used to create a c2cgeoportal project'

    def pre(self, command, output_dir, vars):
        """
        Overrides the base template, adding the "srid" variable to
        the variables list.
        """
        self._set_srid_in_vars(command, vars)
        return BaseTemplate.pre(self, command, output_dir, vars)

    def post(self, command, output_dir, vars):  # pragma: no cover
        """
        Overrides the base template class to print "Welcome to c2cgeoportal!"
        after a successful scaffolding rendering.
        """

        self.out('Welcome to c2cgeoportal!')
        return BaseTemplate.post(self, command, output_dir, vars)

    def _set_srid_in_vars(self, command, vars):
        """
        Set the SRID into the vars dict.
        """
        srid = None
        for arg in command.args:
            m = re.match('srid=(\d+)', arg)
            if m:
                srid = m.group(1)
                break
        if srid is None:
            prompt = 'Spatial Reference System Identifier ' \
                     '(e.g. 21781): '
            srid = input_(prompt).strip()
        try:
            vars['srid'] = int(srid)
        except ValueError:
            raise ValueError(
                'Specified SRID is not an integer')


class TemplateUpdate(BaseTemplate):
    _template_dir = 'update'
    summary = 'Template used to update a c2cgeoportal project'
