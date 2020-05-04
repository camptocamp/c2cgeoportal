# -*- coding: utf-8 -*-

# Copyright (c) 2011-2020, Camptocamp SA
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


import glob
import json
import os
import re
import subprocess
import sys

from pyramid.compat import input_
from pyramid.scaffolds.template import Template
import requests
import yaml


class BaseTemplate(Template):  # pragma: no cover
    """
    A class that can be used as a base class for c2cgeoportal scaffolding
    templates.

    Greatly inspired from ``pyramid.scaffolds.template.PyramidTemplate``.
    """

    def pre(self, command, output_dir, vars_):  # pylint: disable=arguments-differ
        """
        Overrides ``pyramid.scaffold.template.Template.pre``, adding
        several variables to the default variables list. Also prevents
        common misnamings (such as naming a package "site" or naming a
        package logger "root").
        """

        self._get_vars(vars_, "package", "Get a package name: ")
        self._get_vars(vars_, "srid", "Spatial Reference System Identifier (e.g. 2056): ", int)
        srid = vars_["srid"]
        extent = self._epsg2bbox(srid)
        self._get_vars(
            vars_,
            "extent",
            "Extent (minx miny maxx maxy): in EPSG: {srid} projection, default is "
            "[{bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}]: ".format(srid=srid, bbox=extent)
            if extent
            else "Extent (minx miny maxx maxy): in EPSG: {srid} projection: ".format(srid=srid),
        )
        match = re.match(r"([\d.]+)[,; ] *([\d.]+)[,; ] *([\d.]+)[,; ] *([\d.]+)", vars_["extent"])
        if match is not None:
            extent = [match.group(n + 1) for n in range(4)]
        vars_["extent"] = ",".join(extent)
        vars_["extent_mapserver"] = " ".join(extent)

        super().pre(command, output_dir, vars_)

        if vars_["package"] == "site":
            raise ValueError(
                "Sorry, you may not name your package 'site'. "
                "The package name 'site' has a special meaning in "
                "Python.  Please name it anything except 'site'."
            )

        package_logger = vars_["package"]
        if package_logger == "root":
            # Rename the app logger in the rare case a project
            # is named "root"
            package_logger = "app"
        vars_["package_logger"] = package_logger
        vars_["geomapfish_version"] = os.environ["VERSION"]
        vars_["geomapfish_main_version"] = os.environ["MAJOR_VERSION"]

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
                sys.exit(1)

        vars_[name] = value

    @staticmethod
    def _epsg2bbox(srid):
        try:
            r = requests.get("https://epsg.io/?format=json&q={}".format(srid))
            bbox = r.json()["results"][0]["bbox"]
            r = requests.get(
                "https://epsg.io/trans?s_srs=4326&t_srs={srid}&data={bbox[1]},{bbox[0]}".format(
                    srid=srid, bbox=bbox
                )
            )
            r1 = r.json()[0]
            r = requests.get(
                "https://epsg.io/trans?s_srs=4326&t_srs={srid}&data={bbox[3]},{bbox[2]}".format(
                    srid=srid, bbox=bbox
                )
            )
            r2 = r.json()[0]
            return [r1["x"], r2["y"], r2["x"], r1["y"]]
        except requests.RequestException:
            print("Failed to establish a connexion to epsg.io.")
        except json.JSONDecodeError:
            print("epsg.io doesn't return a correct json.")
        except IndexError:
            print("Unable to get the bbox")
        except Exception as exception:
            print("unexpected error: {}".format(str(exception)))
        return None


def fix_executables(output_dir, patterns, in_const_create_template=False):
    if os.name == "posix":
        for pattern in patterns:
            if in_const_create_template:
                pattern = os.path.join(output_dir, "CONST_create_template", pattern)
            else:
                pattern = os.path.join(output_dir, pattern)
            for file_ in glob.glob(pattern):
                subprocess.check_call(["chmod", "+x", file_])


def _gen_authtkt_secret():
    if os.environ.get("CI") == "true":
        return "io7heoDui8xaikie1rushaeGeiph8Bequei6ohchaequob6viejei0xooWeuvohf"
    return subprocess.check_output(["pwgen", "64"]).decode().strip()


class TemplateCreate(BaseTemplate):  # pragma: no cover
    _template_dir = "create"
    summary = "Template used to create a c2cgeoportal project"

    def pre(self, command, output_dir, vars_):
        """
        Overrides the base template
        """
        super().pre(command, output_dir, vars_)
        vars_["authtkt_secret"] = _gen_authtkt_secret()

    def post(self, command, output_dir, vars_):  # pylint: disable=arguments-differ
        """
        Overrides the base template class to print the next step.
        """

        fix_executables(output_dir, ("bin/*", "build", "scripts/publish-docker"))

        super().post(command, output_dir, vars_)


class TemplateUpdate(BaseTemplate):  # pragma: no cover
    _template_dir = "update"
    summary = "Template used to update a c2cgeoportal project"

    @staticmethod
    def open_project(output_dir, vars_):
        project_file = os.path.join(output_dir, "project.yaml")
        if os.path.exists(project_file):
            with open(project_file, "r") as f:
                project = yaml.safe_load(f)
                if "template_vars" in project:
                    for key, value in list(project["template_vars"].items()):
                        vars_[key] = value
        else:
            print("Missing project file: " + project_file)
            sys.exit(1)

    def pre(self, command, output_dir, vars_):
        """
        Overrides the base template
        """
        self.open_project(output_dir, vars_)

        if "authtkt_secret" not in vars_:
            vars_["authtkt_secret"] = _gen_authtkt_secret()

        super().pre(command, output_dir, vars_)

    def post(self, command, output_dir, vars_):  # pylint: disable=arguments-differ
        """
        Overrides the base template class to print "Welcome to c2cgeoportal!"
        after a successful scaffolding rendering.
        """

        fix_executables(output_dir, ("bin/*", "build", "scripts/publish-docker"), True)

        super().post(command, output_dir, vars_)
