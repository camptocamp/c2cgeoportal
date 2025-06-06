# Copyright (c) 2014-2025, Camptocamp SA
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


import argparse
import atexit
import filecmp
import os
import re
import shutil
import subprocess  # nosec
import sys
import tempfile
from argparse import ArgumentParser, Namespace
from collections.abc import Callable
from json.decoder import JSONDecodeError
from subprocess import call, check_call, check_output  # nosec
from typing import Any, cast

import pkg_resources
import requests
import yaml

from c2cgeoportal_geoportal.lib.bashcolor import Color, colorize

REQUIRED_TEMPLATE_KEYS = ["package", "srid", "extent"]
TEMPLATE_EXAMPLE = {"package": "${package}", "srid": "${srid}", "extent": "489246, 78873, 837119, 296543"}
DIFF_NOTICE = (
    "You should apply the changes shown in the diff file on `CONST_create_template/<file>` "
    "on your project's `<file>`.\n"
    "Some advice to be more efficient: if the changes on a file concern a file that you never customize, "
    "you can simply copy the new file from `CONST_create_template` "
    "(`cp CONST_create_template/<file> <file>`)."
    "You can furthermore add this file to the `unmanaged_files` section of the `project.yaml` file, "
    "to avoid its contents appearing in the diff file for the next upgrade."
)


def fix_style() -> None:
    """Fix the style of all the project files using isort, Black and Prettier."""
    if os.path.exists(".pre-commit-config.yaml"):
        print("Run pre-commit to fix the style.")
        sys.stdout.flush()
        subprocess.run(["pre-commit", "run", "--all-files"], check=False)  # pylint: disable=subprocess-run-check


def main() -> None:
    """Tool used to do the application upgrade."""
    parser = _fill_arguments()
    options = parser.parse_args()

    c2cupgradetool = C2cUpgradeTool(options)
    c2cupgradetool.upgrade()


def _fill_arguments() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "--git-remote",
        metavar="GITREMOTE",
        help="Specify the remote branch",
        default="origin",
    )
    parser.add_argument("--step", type=int, help=argparse.SUPPRESS, default=0)

    return parser


class UpgradeInterruptedError(Exception):
    """The interrupted exception."""


_CURRENT_STEP_NUMBER = 0


class Step:
    """Decorator used for en upgrade step."""

    def __init__(self, step_number: int, file_marker: bool = True) -> None:
        global _CURRENT_STEP_NUMBER  # pylint: disable=global-statement # noqa: PLW0603
        _CURRENT_STEP_NUMBER = step_number
        self.step_number = step_number
        self.file_marker = file_marker

    def __call__(
        self,
        current_step: Callable[["C2cUpgradeTool", int], None],
    ) -> Callable[["C2cUpgradeTool"], None]:
        def decorate(c2cupgradetool: "C2cUpgradeTool") -> None:
            try:
                if os.path.isfile(f".UPGRADE{self.step_number - 1}"):
                    os.unlink(f".UPGRADE{self.step_number - 1}")
                if self.file_marker:
                    with open(f".UPGRADE{self.step_number}", "w", encoding="utf8"):
                        pass
                print(f"Start step {self.step_number}.")
                sys.stdout.flush()
                current_step(c2cupgradetool, self.step_number)
            except subprocess.CalledProcessError as exception:
                command = " ".join([f"'{exception}'" for exception in exception.cmd])
                c2cupgradetool.print_step(
                    self.step_number,
                    error=True,
                    message=f"The command `{command}` returns the error code {exception.returncode}.",
                    prompt="Fix the error and run the step again:",
                )
                sys.exit(1)
            except UpgradeInterruptedError as exception:
                c2cupgradetool.print_step(
                    self.step_number,
                    error=True,
                    message=f"There was an error: {exception}.",
                    prompt="Fix the error and run the step again:",
                )
                sys.exit(1)
            except Exception as exception:
                catch_exception = exception

                if self.step_number == _CURRENT_STEP_NUMBER:

                    def message() -> None:
                        c2cupgradetool.print_step(
                            self.step_number,
                            error=True,
                            message=f"The step had the error '{catch_exception}'.",
                            prompt="Fix the error and run the step again:",
                        )

                    atexit.register(message)
                raise

        return decorate


class C2cUpgradeTool:
    """The tool used to upgrade the application."""

    color_bar = colorize("================================================================", Color.GREEN)

    def __init__(self, options: Namespace) -> None:
        self.options = options
        self.project = self.get_project()

    @staticmethod
    def get_project() -> dict[str, Any]:
        if not os.path.isfile("project.yaml"):
            print(colorize("Unable to find the required 'project.yaml' file.", Color.RED))
            sys.exit(1)

        with open("project.yaml", encoding="utf8") as project_file:
            return cast("dict[str, Any]", yaml.safe_load(project_file))

    @staticmethod
    def get_upgrade(section: str) -> list[Any] | dict[str, Any]:
        if not os.path.isfile(".upgrade.yaml"):
            print(colorize("Unable to find the required '.upgrade.yaml' file.", Color.RED))
            sys.exit(1)

        with open(".upgrade.yaml", encoding="utf8") as project_file:
            return cast("list[Any] | dict[str, Any]", yaml.safe_load(project_file)[section])

    def print_step(
        self,
        step: int,
        error: bool = False,
        message: str | None = None,
        prompt: str = "To continue, type:",
    ) -> None:
        with open(".UPGRADE_INSTRUCTIONS", "w", encoding="utf8") as instructions:
            print()
            print(self.color_bar)
            if message is not None:
                print(colorize(message, Color.RED if error else Color.YELLOW))
                instructions.write(f"{message}\n")
            if step >= 0:
                print(colorize(prompt, Color.GREEN))
                instructions.write(f"{prompt}\n")
                cmd = ["./upgrade", os.environ["VERSION"]]
                if step != 0:
                    cmd.append(f"{step}")
                print(colorize(" ".join(cmd), Color.GREEN))
                instructions.write(f"{' '.join(cmd)}\n")

    def run_step(self, step: int) -> None:
        getattr(self, f"step{step}")()

    def test_checkers(self) -> tuple[bool, str | None]:
        headers = " ".join(
            [f"--header {i[0]}={i[1]}" for i in self.project.get("checker_headers", {}).items()],
        )
        run_curl = f"Run `curl --insecure {headers} '{self.project['checker_url']}'` for more information."
        try:
            requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined] # pylint: disable=no-member,unrecognized-inline-option
            resp = requests.get(
                self.project["checker_url"],
                headers=self.project.get("checker_headers"),
                verify=False,  # noqa: S501 # nosec
                timeout=120,
            )
        except requests.exceptions.ConnectionError as exception:
            return False, "\n".join([f"Connection error: {exception}", run_curl])
        except ConnectionRefusedError as exception:
            return False, "\n".join([f"Connection refused: {exception}", run_curl])
        if resp.status_code < 200 or resp.status_code >= 300:
            print(colorize("=============", Color.RED))
            print(colorize("Checker error", Color.RED))
            try:
                for name, value in resp.json()["failures"].items():
                    print(colorize(f"Test '{name}' failed with result:", Color.YELLOW))
                    del value["level"]
                    del value["timing"]

                    print(yaml.dump(value) if value != {} else "No result")
            except JSONDecodeError:
                print(
                    colorize(
                        f"Response is not a JSON '{resp.text}', {resp.reason} {resp.status_code}",
                        Color.RED,
                    ),
                )

            return False, f"Checker error:\n{run_curl}"

        return True, None

    def upgrade(self) -> None:
        self.run_step(self.options.step)

    @Step(0, file_marker=False)
    def step0(self, step: int) -> None:
        project_template_keys = list(cast("dict[str, Any]", self.project.get("template_vars")).keys())
        messages = []
        messages.extend(
            [
                "The element '{required}' is missing in the `template_vars` of "
                "the file 'project.yaml', you should have for example: {required}: {template}.".format(
                    required=required,
                    template=TEMPLATE_EXAMPLE.get(required, ""),
                )
                for required in REQUIRED_TEMPLATE_KEYS
                if required not in project_template_keys
            ],
        )
        if self.project.get("managed_files") is None:
            messages.append(
                "The element `managed_files` is missing in the file 'project.yaml', "
                "you must define this element with a list of regular expressions or with an empty array. "
                "See upgrade documentation for more information.",
            )
        if messages:
            self.print_step(
                step,
                error=True,
                message="\n".join(messages),
                prompt="Fix it and run again the upgrade:",
            )
            sys.exit(1)

        if check_git_status_output() == "":
            self.run_step(step + 1)
        else:
            check_call(["git", "status"])
            self.print_step(
                step + 1,
                message="Here is the output of 'git status'. Please make sure to commit all your "
                "changes before going further. All uncommitted changes will be lost.\n"
                "Note that for debugging purpose it is possible to pass directly to step 2 "
                f"e.-g.: ./upgrade --debug=../c2cgeoportal {os.environ['VERSION']} 2",
            )

    @Step(1)
    def step1(self, step: int) -> None:
        with tempfile.NamedTemporaryFile("w") as project_temp_file:
            shutil.copyfile("project.yaml", project_temp_file.name)
            try:
                check_call(["git", "reset", "--hard"])
                check_call(["git", "clean", "--force", "-d"])
            finally:
                shutil.copyfile(project_temp_file.name, "project.yaml")

        self.run_step(step + 1)

    @Step(2)
    def step2(self, step: int) -> None:
        fix_style()
        subprocess.run(["git", "add", "-A"], check=False)  # pylint: disable=subprocess-run-check
        subprocess.run(["git", "commit", "--message=Run code style"], check=False)  # pylint: disable=subprocess-run-check

        self.run_step(step + 1)

    @Step(3)
    def step3(self, step: int) -> None:
        with tempfile.TemporaryDirectory() as temp_directory_name:
            project_path = os.path.join(temp_directory_name, self.project["project_folder"])
            os.mkdir(project_path)
            shutil.copyfile("/src/project.yaml", os.path.join(project_path, "project.yaml"))
            check_call(
                [
                    "pcreate",
                    "--overwrite",
                    "--scaffold=update",
                    project_path,
                ],
            )
            if self.get_project().get("advance", False):
                check_call(
                    [
                        "pcreate",
                        "--overwrite",
                        "--scaffold=advance_update",
                        project_path,
                    ],
                )

            shutil.copyfile(os.path.join(project_path, ".upgrade.yaml"), ".upgrade.yaml")
            for upgrade_file in cast("list[dict[str, Any]]", self.get_upgrade("upgrade_files")):
                action = upgrade_file["action"]
                if action == "remove":
                    self.files_to_remove(upgrade_file, prefix="CONST_create_template", force=True)
                if action == "move":
                    self.files_to_move(upgrade_file, prefix="CONST_create_template", force=True)

        os.remove(".upgrade.yaml")

        check_call(["git", "add", "--all", "--force", "CONST_create_template/"])
        call(["git", "commit", "--message=Perform the move into the CONST_create_template folder"])

        self.run_step(step + 1)

    @Step(4)
    def step4(self, step: int) -> None:
        if os.path.exists("CONST_create_template"):
            check_call(["git", "rm", "-r", "--force", "CONST_create_template/"])

        with tempfile.TemporaryDirectory() as temp_directory_name:
            project_path = os.path.join(temp_directory_name, self.project["project_folder"])
            check_call(["ln", "-s", "/src", project_path])
            check_call(
                [
                    "pcreate",
                    "--overwrite",
                    "--scaffold=update",
                    project_path,
                ],
            )
            if self.get_project().get("advance", False):
                check_call(
                    [
                        "pcreate",
                        "--overwrite",
                        "--scaffold=advance_update",
                        project_path,
                    ],
                )

        check_call(["git", "add", "--all", "CONST_create_template/"])

        def changed_files() -> list[str]:
            try:
                status = [
                    [s for s in status.strip().split(" ", maxsplit=1) if s]
                    for status in check_git_status_output().strip().split("\n")
                    if status
                ]
                return [
                    file.strip().split(" ")[-1]
                    for state, file in status
                    if state == "M" and not file.strip().startswith("CONST_")
                ]
            except:  # pylint: disable=bare-except
                self.print_step(
                    step,
                    error=True,
                    message=f"Error while getting changed files:\n{check_git_status_output()}",
                    prompt="Fix the error and run the step again:",
                )
                sys.exit(1)

        changed_before_style = changed_files()

        fix_style()

        # Revert code style changes in the project otherwise we get an  error: does not match index
        # on git apply.
        changed_after_style = changed_files()
        to_checkout = [file for file in changed_after_style if file not in changed_before_style]
        if to_checkout:
            subprocess.run(["git", "checkout", *to_checkout], check=True)

        check_call(["git", "add", "--all", "CONST_create_template/"])
        check_call(["git", "clean", "-Xf", "CONST_create_template/"])
        self.run_step(step + 1)

    @Step(5)
    def step5(self, step: int) -> None:
        if "managed_files" not in self.project:
            unmanaged_files = "\n".join(["- " + e for e in self.project.get("unmanaged_files", [])])
            self.print_step(
                step,
                message="In the new version, we will also manage almost all the create template files.\n"
                "By default, files conforming to the following regex pattern will not be replaced:\n"
                f"{unmanaged_files} Therefore, you should fill the 'managed_files' in you 'project.yaml' "
                "file with at least `[]`.",
                prompt="Fill it and run the step again:",
            )
        else:
            self.run_step(step + 1)

    @Step(6)
    def step6(self, step: int) -> None:
        task_to_do = False
        for upgrade_file in cast("list[dict[str, Any]]", self.get_upgrade("upgrade_files")):
            action = upgrade_file["action"]
            if action == "remove":
                task_to_do |= self.files_to_remove(upgrade_file)
            elif action == "move":
                task_to_do |= self.files_to_move(upgrade_file)

        if task_to_do:
            self.print_step(
                step + 1,
                message="""Some `managed_files` or `unmanaged_files` should be updated,
                see message above red and yellow messages to know what should be changed.
                If there is some false positive you should manually revert the changes and
                in the (un)managed files replace the pattern by:

                - pattern: <pattern>
                  no_touch: True
                """,
            )
        else:
            self.run_step(step + 1)

    def files_to_remove(self, element: dict[str, Any], prefix: str = "", force: bool = False) -> bool:
        task_to_do = False
        for path in element["paths"]:
            file_ = os.path.join(prefix, path.format(package=self.project["project_package"]))
            if os.path.exists(file_):
                managed = False
                if not force:
                    for files in self.project["managed_files"]:
                        if isinstance(files, str):
                            pattern = files
                            no_touch = False
                        else:
                            pattern = files["pattern"]
                            no_touch = files.get("no_touch", False)
                        if re.match(pattern + "$", file_):
                            if no_touch:
                                managed = True
                            else:
                                print(
                                    colorize(
                                        f"The file '{file_}' has been removed but he is in the "
                                        f"`managed_files` as '{pattern}'.",
                                        Color.RED,
                                    ),
                                )
                                task_to_do = True
                    for pattern in self.project.get("unmanaged_files", []):
                        if re.match(pattern + "$", file_):
                            print(
                                colorize(
                                    f"The file '{file_}' has been removed but he is in the "
                                    f"`unmanaged_files` as '{pattern}'.",
                                    Color.YELLOW,
                                ),
                            )
                            task_to_do = True
                if not managed:
                    print(f"The file '{file_}' is removed.")
                    if "version" in element and "from" in element:
                        print(
                            f"Was used in version {element['from']}, to be removed from version "
                            f"{element['version']}.",
                        )
                    if os.path.isdir(file_):
                        shutil.rmtree(file_)
                    else:
                        os.remove(file_)
        return task_to_do

    def files_to_move(self, element: dict[str, Any], prefix: str = "", force: bool = False) -> bool:
        task_to_do = False
        src = os.path.join(prefix, element["from"].format(package=self.project["project_package"]))
        dst = os.path.join(prefix, element["to"].format(package=self.project["project_package"]))
        if os.path.exists(src):
            managed = False
            type_ = "directory" if os.path.isdir(src) else "file"
            if not force:
                for files in self.project["managed_files"]:
                    if isinstance(files, str):
                        pattern = files
                        no_touch = False
                    else:
                        pattern = files["pattern"]
                        no_touch = files.get("no_touch", False)
                    if re.match(pattern + "$", src):
                        if no_touch:
                            managed = True
                        else:
                            print(
                                colorize(
                                    f"The {type_} '{src}' is present in the `managed_files` as '{pattern}', "
                                    f"but it has been moved to '{dst}'.",
                                    Color.RED,
                                ),
                            )
                            task_to_do = True
                    if re.match(pattern + "$", dst):
                        print(
                            colorize(
                                f"The {type_} '{dst}' is present in the `managed_files` as '{pattern}', "
                                f"but a file have been moved on it from '{src}'.",
                                Color.RED,
                            ),
                        )
                        task_to_do = True
                for pattern in self.project["unmanaged_files"]:
                    if re.match(pattern + "$", src):
                        print(
                            colorize(
                                f"The {type_} '{src}' is present in the `unmanaged_files` as '{pattern}', "
                                f"but it has been moved to '{dst}'.",
                                Color.YELLOW,
                            ),
                        )
                        task_to_do = True
                    if re.match(pattern + "$", dst):
                        print(
                            colorize(
                                f"The {type_} '{dst}' is present in the `unmanaged_files` as '{pattern}', "
                                f"but a file have been moved on it from '{src}'.",
                                Color.YELLOW,
                            ),
                        )
                        task_to_do = True
            if not managed and os.path.exists(dst) and not element.get("override", False):
                print(colorize(f"The destination '{dst}' already exists, ignoring.", Color.YELLOW))
            elif not managed:
                print(f"Move the {type_} '{src}' to '{dst}'.")
                if "version" in element:
                    print(f"Needed from version {element['version']}.")
                if os.path.dirname(dst) != "":
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    check_call(["git", "mv", src, dst])
                except Exception as exception:  # pylint: disable=broad-exception-caught
                    print(f"[Warning] Git move error: {exception}.")
                    os.rename(src, dst)
        return task_to_do

    @Step(7)
    def step7(self, step: int) -> None:
        self.files_to_get(step)
        self.run_step(step + 1)

    def is_managed(self, file_: str, files_to_get: bool = False) -> bool:
        # Dictionary with:
        # include: list of include regular expression
        # exclude: list of exclude regular expression
        default_project_file = cast("dict[str, list[str]]", self.get_upgrade("default_project_file"))

        # Managed means managed by the application owner, not the c2cupgrade
        managed = False
        if (
            not files_to_get
            or os.path.exists(file_)
            or not check_git_status_output(["CONST_create_template/" + file_]).startswith("A  ")
        ):
            for pattern in default_project_file["include"]:
                if re.match(pattern + "$", file_):
                    print(f"File '{file_}' included by migration config pattern '{pattern}'.")
                    managed = True
                    break
            if managed:
                for pattern in default_project_file["exclude"]:
                    if re.match(pattern + "$", file_):
                        print(f"File '{file_}' excluded by migration config pattern '{pattern}'.")
                        print("managed", file_, pattern)
                        managed = False
                        break
        else:
            print(f"New file '{file_}'.")

        if not managed and not os.path.exists(file_):
            for pattern in self.get_upgrade("extra"):
                if re.match(pattern + "$", file_):
                    print(f"File '{file_}' is an extra by migration config pattern '{pattern}'.")
                    managed = True

        if not managed:
            for files in self.project["managed_files"]:
                pattern = files if isinstance(files, str) else files["pattern"]
                if re.match(pattern + "$", file_):
                    print(f"File '{file_}' included by project config pattern `managed_files` '{pattern}'.")
                    print("managed", file_, pattern)
                    managed = True
                    break
        if managed:
            for pattern in self.project.get("unmanaged_files", []):
                if re.match(pattern + "$", file_):
                    print(f"File '{file_}' excluded by project config pattern `unmanaged_files` '{pattern}'.")
                    managed = False
                    break

        return managed

    def files_to_get(self, step: int, pre: bool = False) -> bool:
        error = False
        for root, _, files in os.walk("CONST_create_template"):
            root = root[len("CONST_create_template/") :]  # noqa: PLW2901
            for file_ in files:
                destination = os.path.join(root, file_)
                managed = self.is_managed(destination, files_to_get=True)
                source = os.path.join("CONST_create_template", destination)
                if not managed and (not os.path.exists(destination) or not filecmp.cmp(source, destination)):
                    print(colorize(f"Get the file '{destination}' from the create template.", Color.GREEN))
                    if not pre:
                        if os.path.dirname(destination) != "":
                            os.makedirs(os.path.dirname(destination), exist_ok=True)
                        try:
                            shutil.copyfile(source, destination)
                            shutil.copymode(source, destination)
                        except PermissionError as exception:
                            self.print_step(
                                step,
                                error=True,
                                message=(
                                    "All your project files should be owned by your user, "
                                    "current error:\n" + str(exception)
                                ),
                                prompt="Fix it and run the upgrade again:",
                            )
                            sys.exit(1)
                elif managed:
                    print(f"The file '{destination}' is managed by the project.")
                elif os.path.exists(destination) and filecmp.cmp(source, destination):
                    print(f"The file '{destination}' does not change.")
                else:
                    print(f"Unknown stat for the file '{destination}'.")
                    sys.exit(2)
        return error

    @Step(8)
    def step8(self, step: int) -> None:
        with open("changelog.diff", "w", encoding="utf8") as diff_file:
            check_call(["git", "diff", "--", "CONST_CHANGELOG.txt"], stdout=diff_file)

        from210 = False
        try:
            check_call(["grep", "--", "-Version 2.1.0", "changelog.diff"])
            from210 = True
        except subprocess.CalledProcessError:
            pass
        if from210:
            check_call(["cp", "CONST_CHANGELOG.txt", "changelog.diff"])

        if os.path.getsize("changelog.diff") == 0:
            self.run_step(step + 1)
        else:
            self.print_step(
                step + 1,
                message="Apply the manual migration steps based on what is in the CONST_CHANGELOG.txt "
                "file (listed in the `changelog.diff` file).",
            )

    def get_modified(self, status_path: str) -> list[str]:
        status = check_git_status_output([status_path]).split("\n")
        status = [s for s in status if len(s) > 3]
        status = [s[3:] for s in status if s[:3].strip() == "M"]
        for pattern in self.get_upgrade("no_diff"):
            matcher = re.compile(f"CONST_create_template/{pattern}$")
            status = [s for s in status if not matcher.match(s)]
        status = [s for s in status if os.path.exists(s[len("CONST_create_template/") :])]
        return [s for s in status if not filecmp.cmp(s, s[len("CONST_create_template/") :])]

    @Step(9)
    def step9(self, step: int) -> None:
        if os.path.isfile("changelog.diff"):
            os.unlink("changelog.diff")

        status = self.get_modified(
            f"CONST_create_template/geoportal/{self.project['project_package']}_geoportal/static-ngeo",
        )
        status += ["CONST_create_template/geoportal/vars.yaml"]

        with open("ngeo.diff", "w", encoding="utf8") as diff_file:
            if status:
                check_call(
                    ["git", "diff", "--relative=CONST_create_template", "--staged", "--", *status],
                    stdout=diff_file,
                )

        if os.path.getsize("ngeo.diff") == 0:
            self.run_step(step + 1)
        else:
            self.print_step(
                step + 1,
                message="Manually apply the ngeo application changes as shown in the `ngeo.diff` file.\n"
                + DIFF_NOTICE
                + "\nNote that you can also apply them using: git apply --3way ngeo.diff",
            )

    @Step(10)
    def step10(self, step: int) -> None:
        if os.path.isfile("ngeo.diff"):
            os.unlink("ngeo.diff")

        status = self.get_modified("CONST_create_template")
        status = [
            s
            for s in status
            if not s.startswith(
                f"CONST_create_template/geoportal/{self.project['project_package']}_geoportal/static-ngeo/",
            )
        ]
        status = [s for s in status if s != "CONST_create_template/geoportal/vars.yaml"]

        if status:
            with open("create.diff", "w", encoding="utf8") as diff_file:
                if status:
                    check_call(
                        ["git", "diff", "--relative=CONST_create_template", "--staged", "--", *status],
                        stdout=diff_file,
                    )

            if os.path.getsize("create.diff") == 0:
                self.run_step(step + 1)
            else:
                self.print_step(
                    step + 1,
                    message="The `create.diff` file is a recommendation of the changes that you "
                    "should apply to your project.\n"
                    + DIFF_NOTICE
                    + "\nNote that you can also apply them using: git apply --3way create.diff",
                )
        else:
            self.run_step(step + 1)

    @Step(11)
    def step11(self, step: int) -> None:
        if os.path.isfile("create.diff"):
            os.unlink("create.diff")

        fix_style()

        message = [
            "The upgrade is nearly done, now you should:",
            "- Build your application with `./upgrade --finalize [build arguments]`",
            f"- Test your application on '{self.project.get('application_url', '... missing ...')}'.",
        ]

        if os.path.isfile(".upgrade.yaml"):
            os.unlink(".upgrade.yaml")
        with open(".UPGRADE_SUCCESS", "w", encoding="utf8"):
            pass
        self.print_step(step + 1, message="\n".join(message))

    @Step(12, file_marker=False)
    def step12(self, step: int) -> None:
        if os.path.isfile(".UPGRADE_SUCCESS"):
            os.unlink(".UPGRADE_SUCCESS")
        good, message = self.test_checkers()
        if good:
            self.run_step(step + 1)
        else:
            self.print_step(
                step,
                error=True,
                message=message,
                prompt="Correct the checker, then run the step again "
                "(If you want to fix it later you can pass to the next step:int):",
            )
            sys.exit(1)

    @Step(13, file_marker=False)
    def step13(self, step: int) -> None:
        # Required to remove from the Git stage the ignored file when we lunch the step again
        check_call(["git", "reset", "--mixed"])

        check_call(["git", "add", "--all"])
        check_call(["git", "status"])

        self.print_step(
            step + 1,
            message="We will commit all the above files!\n"
            "If there are some files which should not be committed, then you should "
            f"add them into the `.gitignore` file and launch upgrade {step} again.",
            prompt="Then to commit your changes type:",
        )

    @Step(14, file_marker=False)
    def step14(self, _: int) -> None:
        if os.path.isfile(".UPGRADE_INSTRUCTIONS"):
            os.unlink(".UPGRADE_INSTRUCTIONS")
        check_call(
            [
                "git",
                "commit",
                "--message=Upgrade to GeoMapFish "
                f"{pkg_resources.get_distribution('c2cgeoportal_commons').version}",
            ],
        )

        print()
        print(self.color_bar)
        print()
        print(colorize("Congratulations, your upgrade was successful.", Color.GREEN))
        print()
        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
        print("Now all your files are committed; you should do a git push:")
        print(f"git push {self.options.git_remote} {branch}.")


def check_git_status_output(args: list[str] | None = None) -> str:
    """Check if there is something that's not committed."""
    return check_output(["git", "status", "--short"] + (args if args is not None else [])).decode("utf-8")


if __name__ == "__main__":
    main()
