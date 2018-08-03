# -*- coding: utf-8 -*-

# Copyright (c) 2012-2018, Camptocamp SA
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
import subprocess
import os
import glob
import json
import requests
import yaml
import pkg_resources

from pyramid.scaffolds.template import Template
from pyramid.compat import input_


class BaseTemplate(Template):  # pragma: no cover
    """
    A class that can be used as a base class for c2cgeoportal scaffolding
    templates.

    Greatly inspired from ``pyramid.scaffolds.template.PyramidTemplate``.
    """

    def pre(self, command, output_dir, vars_):
        """
        Overrides ``pyramid.scaffold.template.Template.pre``, adding
        several variables to the default variables list. Also prevents
        common misnamings (such as naming a package "site" or naming a
        package logger "root").
        """

        self._get_vars(vars_, "package", "Get a package name: ")
        self._get_vars(
            vars_, "srid",
            "Spatial Reference System Identifier (e.g. 21781): ", int,
        )
        srid = vars_["srid"]
        extent = self._epsg2bbox(srid)
        self._get_vars(
            vars_, "extent",
            "Extent (minx miny maxx maxy): in EPSG: {srid} projection, default is "
            "[{bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}]: ".format(srid=srid, bbox=extent)
            if extent else
            "Extent (minx miny maxx maxy): in EPSG: {srid} projection: ".format(srid=srid)
        )
        match = re.match(r"([\d.]+)[,; ] *([\d.]+)[,; ] *([\d.]+)[,; ] *([\d.]+)", vars_["extent"])
        if match is not None:
            extent = [match.group(n + 1) for n in range(4)]
        vars_["extent"] = ",".join(extent)
        vars_["extent_mapserver"] = " ".join(extent)
        vars_["extent_viewer"] = json.dumps(extent)

        ret = Template.pre(self, command, output_dir, vars_)

        if vars_["package"] == "site":
            raise ValueError(
                "Sorry, you may not name your package 'site'. "
                "The package name 'site' has a special meaning in "
                "Python.  Please name it anything except 'site'.")

        package_logger = vars_["package"]
        if package_logger == "root":
            # Rename the app logger in the rare case a project
            # is named "root"
            package_logger = "app"
        vars_["package_logger"] = package_logger
        vars_["geomapfish_version"] = pkg_resources.get_distribution('c2cgeoportal_commons').version

        return ret

    @staticmethod
    def out(msg):
        print(msg)

    @staticmethod
    def _get_vars(vars_, name, prompt, type_=None):
        """
        Set an attribute in the vars dict.
        """

        if name.upper() in os.environ and os.environ[name.upper()] != "":
            value = os.environ[name.upper()]
        else:
            value = vars_.get(name)

        if value is None:
            value = input_(prompt).strip()

        if type_ is not None and not isinstance(value, type_):
            try:
                type_(value)
            except ValueError:
                print(("The attribute {}={} is not a {}".format(name, value, type_)))
                exit(1)

        vars_[name] = value

    @staticmethod
    def _epsg2bbox(srid):
        try:
            r = requests.get("http://epsg.io/?format=json&q={}".format(srid))
            bbox = r.json()["results"][0]["bbox"]
            r = requests.get(
                "http://epsg.io/trans?s_srs=4326&t_srs={srid}&data={bbox[1]},{bbox[0]}"
                        .format(srid=srid, bbox=bbox)
            )
            r1 = r.json()[0]
            r = requests.get(
                "http://epsg.io/trans?s_srs=4326&t_srs={srid}&data={bbox[3]},{bbox[2]}"
                        .format(srid=srid, bbox=bbox)
            )
            r2 = r.json()[0]
            return [r1["x"], r2["y"], r2["x"], r1["y"]]
        except requests.RequestException:
            print("Failed to establish a connexion to epsg.io.")
            return None
        except json.JSONDecodeError:
            print("epsg.io doesn't return a correct json.")
            return None
        except IndexError:
            print("Unable to get the bbox")
            return None


def fix_executables(output_dir, patterns, in_const_create_template=False):
    if os.name == 'posix':
        for pattern in patterns:
            if in_const_create_template:
                pattern = os.path.join(output_dir, "CONST_create_template", pattern)
            else:
                pattern = os.path.join(output_dir, pattern)
            for file_ in glob.glob(pattern):
                subprocess.check_call(["chmod", "+x", file_])


class TemplateCreate(BaseTemplate):  # pragma: no cover
    _template_dir = "create"
    summary = "Template used to create a c2cgeoportal project"

    def post(self, command, output_dir, vars_):
        """
        Overrides the base template class to print the next step.
        """

        fix_executables(output_dir, ("docker-run", "docker-compose-run", "bin/*"))

        return BaseTemplate.post(self, command, output_dir, vars_)


class TemplateUpdate(BaseTemplate):  # pragma: no cover
    _template_dir = "update"
    summary = "Template used to update a c2cgeoportal project"

    @staticmethod
    def open_project(vars_):
        if os.path.exists("project.yaml"):
            with open("project.yaml", "r") as f:
                project = yaml.safe_load(f)
                if "template_vars" in project:
                    for key, value in list(project["template_vars"].items()):
                        vars_[key] = value

    def pre(self, command, output_dir, vars_):
        """
        Overrides the base template
        """
        self.open_project(vars_)
        return BaseTemplate.pre(self, command, output_dir, vars_)

    def post(self, command, output_dir, vars_):
        """
        Overrides the base template class to print "Welcome to c2cgeoportal!"
        after a successful scaffolding rendering.
        """

        fix_executables(output_dir, ("docker-run", "docker-compose-run", "bin/*"), True)

        return BaseTemplate.post(self, command, output_dir, vars_)


class TemplateNondockerCreate(TemplateCreate):  # pragma: no cover
    _template_dir = "nondockercreate"
    summary = "Template used to create a non Docker c2cgeoportal project"

    def pre(self, command, output_dir, vars_):
        self._get_vars(vars_, "apache_vhost", "The Apache vhost name: ")
        return super().pre(command, output_dir, vars_)

    def post(self, command, output_dir, vars_):
        fix_executables(output_dir, ("get-pip-dependencies", "deploy/hooks/*"))

        return super().post(command, output_dir, vars_)


class TemplateNondockerUpdate(TemplateUpdate):  # pragma: no cover
    _template_dir = "nondockerupdate"
    summary = "Template used to update a non Docker c2cgeoportal project"

    def pre(self, command, output_dir, vars_):
        self.open_project(vars_)
        self._get_vars(vars_, "apache_vhost", "The Apache vhost name: ")
        return BaseTemplate.pre(self, command, output_dir, vars_)

    def post(self, command, output_dir, vars_):
        fix_executables(output_dir, ("get-pip-dependencies", "deploy/hooks/*"), True)

        return BaseTemplate.post(self, command, output_dir, vars_)
