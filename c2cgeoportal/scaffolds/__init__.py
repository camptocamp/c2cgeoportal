# -*- coding: utf-8 -*-

# Copyright (c) 2012-2014, Camptocamp SA
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


import re
from os import path
from yaml import load
from six import string_types

from pyramid.scaffolds.template import Template
from pyramid.compat import input_


class BaseTemplate(Template):  # pragma: no cover
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

        if vars["package"] == "site":
            raise ValueError(
                "Sorry, you may not name your package 'site'. "
                "The package name 'site' has a special meaning in "
                "Python.  Please name it anything except 'site'.")

        package_logger = vars["package"]
        if package_logger == "root":
            # Rename the app logger in the rare case a project
            # is named "root"
            package_logger = "app"
        vars["package_logger"] = package_logger

        return ret

    def _set_package_in_vars(self, command, vars):
        """
        Set the package into the vars dict.
        """
        for arg in command.args:
            m = re.match("package=(\w+)", arg)
            if m:
                vars["package"] = m.group(1)
                break

    def out(self, msg):
        print(msg)


class TemplateCreate(BaseTemplate):  # pragma: no cover
    _template_dir = "create"
    summary = "Template used to create a c2cgeoportal project"

    def pre(self, command, output_dir, vars):
        """
        Overrides the base template, adding the "srid" variable to
        the variables list.
        """
        self._set_srid_in_vars(command, vars)
        return BaseTemplate.pre(self, command, output_dir, vars)

    def post(self, command, output_dir, vars):
        """
        Overrides the base template class to print "Welcome to c2cgeoportal!"
        after a successful scaffolding rendering.
        """

        self.out("Welcome to c2cgeoportal!")
        return BaseTemplate.post(self, command, output_dir, vars)

    def _set_srid_in_vars(self, command, vars):
        """
        Set the SRID into the vars dict.
        """
        srid = None
        for arg in command.args:
            m = re.match("srid=(\d+)", arg)
            if m:
                srid = m.group(1)
                break
        if srid is None:
            prompt = "Spatial Reference System Identifier " \
                     "(e.g. 21781): "
            srid = input_(prompt).strip()
        try:
            vars["srid"] = int(srid)
        except ValueError:
            raise ValueError(
                "Specified SRID is not an integer")


class TemplateUpdate(BaseTemplate):  # pragma: no cover
    _template_dir = "update"
    summary = "Template used to update a c2cgeoportal project"

    def pre(self, command, output_dir, vars):
        """
        Overrides the base template
        """

        if path.exists("project.yaml"):
            project = load(file("project.yaml", "r"))
            if "template_vars" in project:
                for key, value in project["template_vars"].items():
                    if isinstance(value, string_types):
                        vars[key] = value.encode("utf-8")

        return BaseTemplate.pre(self, command, output_dir, vars)
