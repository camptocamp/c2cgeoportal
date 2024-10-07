# Copyright (c) 2021-2024, Camptocamp SA
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


import json
import os
import re
import subprocess
import sys
from argparse import ArgumentParser
from typing import Any, Union, cast

import pkg_resources
import requests
import yaml
from cookiecutter.log import configure_logger
from cookiecutter.main import cookiecutter

_bad_chars_re = re.compile("[^a-zA-Z0-9_]")
SCAFFOLDS_DIR = pkg_resources.resource_filename("c2cgeoportal_geoportal", "scaffolds")


def get_argparser() -> ArgumentParser:
    """Get the argument parser for this script."""

    parser = ArgumentParser(
        prog=sys.argv[0],
        add_help=True,
        description="Wrapper around cookiecutter that create appropriated context.",
    )
    parser.add_argument(
        "-s",
        "--scaffold",
        dest="scaffold_names",
        action="append",
        help=("Add a scaffold to the create process " "(multiple -s args accepted)"),
    )
    parser.add_argument(
        "-l",
        "--list",
        dest="list",
        action="store_true",
        help="List all available scaffold names",
    )
    parser.add_argument(
        "--package-name",
        dest="package_name",
        action="store",
        help="Package name to use. The name provided is "
        "assumed to be a valid Python package name, and "
        "will not be validated. By default the package "
        "name is derived from the value of "
        "output_directory.",
    )
    parser.add_argument(
        "--overwrite",
        dest="overwrite",
        action="store_true",
        help="Always overwrite",
    )
    parser.add_argument(
        "output_directory",
        nargs="?",
        default=None,
        help="The directory where the project will be " "created.",
    )
    return parser


def main() -> int:
    """Entry point to run PCreateCommand."""
    command = PCreateCommand(sys.argv)
    try:
        return command.run()
    except KeyboardInterrupt:  # pragma: no cover
        return 1


class PCreateCommand:
    """
    Wrapper around cookiecutter with appropriated context creator for our scaffolds.

    This is a port of Pyramid 1 PCreateCommand using cookiecutter as a backend.
    """

    def __init__(self, argv: list[str], quiet: bool = False) -> None:
        self.quiet = quiet
        self.parser = get_argparser()
        self.args = self.parser.parse_args(argv[1:])
        self.scaffolds = self.all_scaffolds()

    def run(self) -> int:
        if self.args.list:
            return self.show_scaffolds()
        if not self.args.scaffold_names and not self.args.output_directory:
            if not self.quiet:  # pragma: no cover
                self.parser.print_help()
                self.out("")
                self.show_scaffolds()
            return 2

        return self.render_scaffolds()

    @property
    def output_path(self) -> str:
        return cast(str, os.path.abspath(os.path.normpath(self.args.output_directory)))

    def render_scaffolds(self) -> int:
        verbose = True
        debug_file = None
        configure_logger(stream_level="DEBUG" if verbose else "INFO", debug_file=debug_file)

        context = self.get_context()

        for scaffold_name in self.args.scaffold_names:
            # Needed to be backward compatible for the `test-upgrade init` command
            if scaffold_name.startswith("c2cgeoportal_"):
                scaffold_name = scaffold_name[len("c2cgeoportal_") :]
            self.out(f"Rendering scaffold: {scaffold_name}")
            cookiecutter(
                template=os.path.join(SCAFFOLDS_DIR, scaffold_name),
                extra_context=context,
                no_input=True,
                overwrite_if_exists=self.args.overwrite,
                output_dir=os.path.dirname(self.output_path),
            )
        return 0

    def show_scaffolds(self) -> int:
        scaffolds = sorted(self.scaffolds)
        if scaffolds:
            self.out("Available scaffolds:")
            for scaffold in scaffolds:
                self.out(f"  {scaffold}")
        else:
            self.out("No scaffolds available")
        return 0

    @staticmethod
    def all_scaffolds() -> list[str]:
        return os.listdir(SCAFFOLDS_DIR)

    def out(self, msg: str) -> None:
        if not self.quiet:
            print(msg)

    def get_context(self) -> dict[str, str | int]:
        output_dir = self.output_path
        project_name = os.path.basename(output_dir)
        if self.args.package_name is None:
            pkg_name = _bad_chars_re.sub("", project_name.lower().replace("-", "_"))
        else:
            pkg_name = self.args.package_name

        context: dict[str, str | int] = {
            "project": project_name,
            "package": pkg_name,
            "authtkt_secret": gen_authtkt_secret(),
        }
        context.update(self.read_project_file())
        if os.environ.get("CI") == "true":
            context["authtkt_secret"] = (  # nosec
                "io7heoDui8xaikie1rushaeGeiph8Bequei6ohchaequob6viejei0xooWeuvohf"
            )

        self.get_var(context, "srid", "Spatial Reference System Identifier (e.g. 2056): ", int)
        srid = cast(int, context["srid"])
        extent = self.epsg2bbox(srid)
        self.get_var(
            context,
            "extent",
            (
                f"Extent (minx miny maxx maxy): in EPSG: {srid} projection, default is "
                f"[{extent[0]} {extent[1]} {extent[2]} {extent[3]}]: "
                if extent
                else f"Extent (minx miny maxx maxy): in EPSG: {srid} projection: "
            ),
        )
        match = re.match(
            r"([\d.]+)[,; ] *([\d.]+)[,; ] *([\d.]+)[,; ] *([\d.]+)",
            cast(str, context["extent"]),
        )
        if match is not None:
            extent = [match.group(n + 1) for n in range(4)]
        assert extent is not None
        context["extent"] = ",".join(extent)
        context["extent_mapserver"] = " ".join(extent)

        if context["package"] == "site":
            raise ValueError(
                "Sorry, you may not name your package 'site'. "
                "The package name 'site' has a special meaning in "
                "Python.  Please name it anything except 'site'."
            )

        package_logger = context["package"]
        if package_logger == "root":
            # Rename the app logger in the rare case a project
            # is named "root"
            package_logger = "app"
        context["package_logger"] = package_logger
        context["geomapfish_version"] = os.environ["VERSION"]
        # Used in the Docker files to shoos the version of the build image
        context["geomapfish_version_tag"] = "GEOMAPFISH_VERSION"
        context["geomapfish_version_tag_env"] = "${GEOMAPFISH_VERSION}"
        geomapfish_major_version_tag = (
            "GEOMAPFISH_VERSION"
            if context.get("unsafe_long_version", False)
            else "GEOMAPFISH_MAIN_MINOR_VERSION"
        )
        # Used in the Docker files to shoos the version of the run image
        context["geomapfish_major_version_tag"] = geomapfish_major_version_tag
        context["geomapfish_major_version_tag_env"] = "${" + geomapfish_major_version_tag + "}"
        context["geomapfish_main_version"] = os.environ["MAJOR_VERSION"]
        context["geomapfish_main_version_dash"] = os.environ["MAJOR_VERSION"].replace(".", "-")
        context["geomapfish_main_minor_version"] = os.environ["MAJOR_MINOR_VERSION"]

        return context

    def read_project_file(self) -> dict[str, str | int]:
        project_file = os.path.join(self.output_path, "project.yaml")
        if os.path.exists(project_file):
            with open(project_file, encoding="utf8") as f:
                project = yaml.safe_load(f)
                return cast(dict[str, Union[str, int]], project.get("template_vars", {}))
        else:
            return {}

    @staticmethod
    def get_var(
        context: dict[str, Any],
        name: str,
        prompt: str,
        type_: type[Any] | None = None,
    ) -> None:
        if name.upper() in os.environ and os.environ[name.upper()] != "":
            value = os.environ.get(name.upper())
        else:
            value = context.get(name)

        if value is None:
            value = input(prompt).strip()

        if type_ is not None and not isinstance(value, type_):
            try:
                value = type_(value)
            except ValueError:
                print(f"The attribute {name}={value} is not a {type_}")
                sys.exit(1)

        context[name] = value

    @staticmethod
    def epsg2bbox(srid: int) -> list[str] | None:
        try:
            r = requests.get(f"https://epsg.io/?format=json&q={srid}", timeout=60)
            bbox = r.json()["results"][0]["bbox"]
            r = requests.get(
                "https://epsg.io/trans?s_srs=4326&t_srs={srid}&data={bbox[1]},{bbox[0]}".format(
                    srid=srid, bbox=bbox
                ),
                timeout=60,
            )
            r1 = r.json()[0]
            r = requests.get(
                "https://epsg.io/trans?s_srs=4326&t_srs={srid}&data={bbox[3]},{bbox[2]}".format(
                    srid=srid, bbox=bbox
                ),
                timeout=60,
            )
            r2 = r.json()[0]
            return [r1["x"], r2["y"], r2["x"], r1["y"]]
        except requests.RequestException:
            print("Failed to establish a connection to epsg.io.")
        except json.JSONDecodeError:
            print("epsg.io doesn't return a correct json.")
        except IndexError:
            print("Unable to get the bbox")
        except Exception as exception:  # pylint: disable=broad-exception-caught
            print(f"unexpected error: {str(exception)}")
        return None


def gen_authtkt_secret() -> str:
    """Generate a random authtkt secret."""
    return subprocess.run(["pwgen", "64"], stdout=subprocess.PIPE, check=True).stdout.decode().strip()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main() or 0)
