# -*- coding: utf-8 -*-

# Copyright (c) 2014-2020, Camptocamp SA
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
from argparse import ArgumentParser
import atexit
import filecmp
import os
import re
import shutil
import subprocess
from subprocess import call, check_call, check_output
import sys
from typing import Any, Dict, cast

import pkg_resources
import requests
import yaml

from c2cgeoportal_geoportal.lib.bashcolor import GREEN, RED, YELLOW, colorize

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


def main():
    """
    tool used to do the application upgrade
    """

    parser = _fill_arguments()
    options = parser.parse_args()

    c2cupgradetool = C2cUpgradeTool(options)
    c2cupgradetool.upgrade()


def _fill_arguments():
    parser = ArgumentParser()
    parser.add_argument("version", nargs="?", help="No more used")
    parser.add_argument(
        "--git-remote", metavar="GITREMOTE", help="Specify the remote branch", default="origin"
    )
    parser.add_argument("--step", type=int, help=argparse.SUPPRESS, default=0)

    return parser


class InteruptedException(Exception):
    pass


current_step_number = 0


class Step:
    def __init__(self, step_number, file_marker=True):
        global current_step_number
        current_step_number = step_number
        self.step_number = step_number
        self.file_marker = file_marker

    def __call__(self, current_step):
        def decorate(c2cupgradetool, *args, **kwargs):
            try:
                if os.path.isfile(".UPGRADE{}".format(self.step_number - 1)):
                    os.unlink(".UPGRADE{}".format(self.step_number - 1))
                if self.file_marker:
                    with open(".UPGRADE{}".format(self.step_number), "w"):
                        pass
                print("Start step {}.".format(self.step_number))
                sys.stdout.flush()
                current_step(c2cupgradetool, self.step_number, *args, **kwargs)
            except subprocess.CalledProcessError as exception:
                c2cupgradetool.print_step(
                    self.step_number,
                    error=True,
                    message="The command `{}` returns the error code {}.".format(
                        " ".join(["'{}'".format(exception) for exception in exception.cmd]),
                        exception.returncode,
                    ),
                    prompt="Fix the error and run the step again:",
                )
                sys.exit(1)
            except InteruptedException as exception:
                c2cupgradetool.print_step(
                    self.step_number,
                    error=True,
                    message="There was an error: {}.".format(exception),
                    prompt="Fix the error and run the step again:",
                )
                sys.exit(1)
            except Exception as exception:
                cautch_exception = exception

                global current_step_number
                if self.step_number == current_step_number:

                    def message():
                        c2cupgradetool.print_step(
                            self.step_number,
                            error=True,
                            message="The step had the error '{}'.".format(cautch_exception),
                            prompt="Fix the error and run the step again:",
                        )

                    atexit.register(message)
                raise

        return decorate


class C2cUpgradeTool:

    color_bar = colorize("================================================================", GREEN)

    def __init__(self, options):
        self.options = options
        self.project: Dict[str, Any] = self.get_project()

    @staticmethod
    def get_project():
        if not os.path.isfile("project.yaml"):
            print(colorize("Unable to find the required 'project.yaml' file.", RED))
            sys.exit(1)

        with open("project.yaml", "r") as project_file:
            return yaml.safe_load(project_file)

    @staticmethod
    def get_upgrade(section):
        if not os.path.isfile(".upgrade.yaml"):
            print(colorize("Unable to find the required '.upgrade.yaml' file.", RED))
            sys.exit(1)

        with open(".upgrade.yaml", "r") as project_file:
            return yaml.safe_load(project_file)[section]

    def print_step(self, step, error=False, message=None, prompt="To continue, type:"):
        with open(".UPGRADE_INSTRUCTIONS", "w") as instructions:
            print("")
            print(self.color_bar)
            if message is not None:
                print(colorize(message, RED if error else YELLOW))
                instructions.write("{}\n".format(message))
            if step >= 0:
                print(colorize(prompt, GREEN))
                instructions.write("{}\n".format(prompt))
                cmd = ["./upgrade", os.environ["VERSION"]]
                if step != 0:
                    cmd.append("{}".format(step))
                print(colorize(" ".join(cmd), GREEN))
                instructions.write("{}\n".format(" ".join(cmd)))

    def run_step(self, step):
        getattr(self, "step{}".format(step))()

    def test_checkers(self):
        run_curl = "Run `curl --insecure {} '{}'` for more information.".format(
            " ".join(["--header {}={}".format(*i) for i in self.project.get("checker_headers", {}).items()]),
            self.project["checker_url"],
        )
        try:
            requests.packages.urllib3.disable_warnings()
            resp = requests.get(
                self.project["checker_url"], headers=self.project.get("checker_headers"), verify=False
            )
        except requests.exceptions.ConnectionError as exception:
            return False, "\n".join(["Connection error: {}".format(exception), run_curl])
        except ConnectionRefusedError as exception:
            return False, "\n".join(["Connection refused: {}".format(exception), run_curl])
        if resp.status_code < 200 or resp.status_code >= 300:

            print(colorize("=============", RED))
            print(colorize("Checker error", RED))
            for name, value in resp.json()["failures"].items():
                print(colorize("Test '{}' failed with result:".format(name), YELLOW))
                del value["level"]
                del value["timing"]

                print(yaml.dump(value) if value != {} else "No result")

            return False, "\n".join(["Checker error:", run_curl])

        return True, None

    def upgrade(self):
        self.run_step(self.options.step)

    @Step(0, file_marker=False)
    def step0(self, step):
        project_template_keys = list(cast(Dict[str, Any], self.project.get("template_vars")).keys())
        messages = []
        for required in REQUIRED_TEMPLATE_KEYS:
            if required not in project_template_keys:
                messages.append(
                    "The element '{required}' is missing in the `template_vars` of "
                    "the file 'project.yaml', you should have for example: {required}: {template}.".format(
                        required=required, template=TEMPLATE_EXAMPLE.get("required", "")
                    )
                )
        if self.project.get("managed_files") is None:
            messages.append(
                "The element `managed_files` is missing in the file 'project.yaml', "
                "you must define this element with a list of regular expressions or with an empty array. "
                "See upgrade documentation for more information."
            )
        if messages:
            self.print_step(
                step, error=True, message="\n".join(messages), prompt="Fix it and run again the upgrade:"
            )
            sys.exit(1)

        if check_git_status_output() == "":
            self.run_step(step + 1)
        else:
            check_call(["git", "status"])
            self.print_step(
                step + 1,
                message="Here is the output of 'git status'. Please make sure to commit all your "
                "changes before going further. All uncommitted changes will be lost.",
            )

    @Step(1)
    def step1(self, step):
        shutil.copyfile("project.yaml", "/tmp/project.yaml")
        try:
            check_call(["git", "reset", "--hard"])
            check_call(["git", "clean", "--force", "-d"])
        finally:
            shutil.copyfile("/tmp/project.yaml", "project.yaml")

        self.run_step(step + 1)

    @Step(2)
    def step2(self, step):
        project_path = os.path.join("/tmp", self.project["project_folder"])
        os.mkdir(project_path)
        shutil.copyfile("/src/project.yaml", os.path.join(project_path, "project.yaml"))
        check_call(
            [
                "pcreate",
                "--ignore-conflicting-name",
                "--overwrite",
                "--scaffold=c2cgeoportal_update",
                project_path,
            ]
        )

        shutil.copyfile(os.path.join(project_path, ".upgrade.yaml"), ".upgrade.yaml")
        for upgrade_file in self.get_upgrade("upgrade_files"):
            action = upgrade_file["action"]
            if action == "remove":
                self.files_to_remove(upgrade_file, prefix="CONST_create_template", force=True)
            if action == "move":
                self.files_to_move(upgrade_file, prefix="CONST_create_template", force=True)

        shutil.rmtree(project_path)
        os.remove(".upgrade.yaml")

        check_call(["git", "add", "--all", "--force", "CONST_create_template/"])
        call(["git", "commit", "--message=Perform the move into the CONST_create_template folder"])

        self.run_step(step + 1)

    @Step(3)
    def step3(self, step):
        if os.path.exists("CONST_create_template"):
            check_call(["git", "rm", "-r", "--force", "CONST_create_template/"])

        project_path = os.path.join("/tmp", self.project["project_folder"])
        check_call(["ln", "-s", "/src", project_path])
        check_call(
            [
                "pcreate",
                "--ignore-conflicting-name",
                "--overwrite",
                "--scaffold=c2cgeoportal_update",
                project_path,
            ]
        )
        os.remove(project_path)

        check_call(["git", "add", "--all", "CONST_create_template/"])
        check_call(["git", "clean", "-Xf", "CONST_create_template/"])
        self.run_step(step + 1)

    @Step(4)
    def step4(self, step):
        if "managed_files" not in self.project:
            self.print_step(
                step,
                message="In the new version, we will also manage almost all the create "
                "template files.\n"
                "By default, files conforming to the following regex pattern will not be replaced:\n{}"
                "Therefore, you should fill the 'managed_files' in you 'project.yaml' file with at least "
                "`[]`.".format("\n".join(["- " + e for e in self.project.get("unmanaged_files", [])])),
                prompt="Fill it and run the step again:",
            )
        else:
            self.run_step(step + 1)

    @Step(5)
    def step5(self, step):
        task_to_do = False
        for upgrade_file in self.get_upgrade("upgrade_files"):
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

    def files_to_remove(self, element, prefix="", force=False):
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
                                # fmt: off
                                print(colorize(
                                    "The file '{}' has been removed but he is in the `managed_files` as '{}'."
                                    .format(file_, pattern),
                                    RED
                                ))
                                # fmt: on
                                task_to_do = True
                    for pattern in self.project.get("unmanaged_files", []):
                        if re.match(pattern + "$", file_):
                            # fmt: off
                            print(colorize(
                                "The file '{}' has been removed but he is in the `unmanaged_files` as '{}'."
                                .format(file_, pattern),
                                YELLOW
                            ))
                            # fmt: on
                            task_to_do = True
                if not managed:
                    print("The file '{}' is removed.".format(file_))
                    if "version" in element and "from" in element:
                        print(
                            "Was used in version {}, to be removed from version {}.".format(
                                element["from"], element["version"]
                            )
                        )
                    if os.path.isdir(file_):
                        shutil.rmtree(file_)
                    else:
                        os.remove(file_)
        return task_to_do

    def files_to_move(self, element, prefix="", force=False):
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
                                    "The {} '{}' is present in the `managed_files` as '{}', "
                                    "but it has been moved to '{}'.".format(type_, src, pattern, dst),
                                    RED,
                                )
                            )
                            task_to_do = True
                    if re.match(pattern + "$", dst):
                        print(
                            colorize(
                                "The {} '{}' is present in the `managed_files` as '{}', "
                                "but a file have been moved on it from '{}'.".format(
                                    type_, dst, pattern, src
                                ),
                                RED,
                            )
                        )
                        task_to_do = True
                for pattern in self.project["unmanaged_files"]:
                    if re.match(pattern + "$", src):
                        print(
                            colorize(
                                "The {} '{}' is present in the `unmanaged_files` as '{}', "
                                "but it has been moved to '{}'.".format(type_, src, pattern, dst),
                                YELLOW,
                            )
                        )
                        task_to_do = True
                    if re.match(pattern + "$", dst):
                        print(
                            colorize(
                                "The {} '{}' is present in the `unmanaged_files` as '{}', "
                                "but a file have been moved on it from '{}'.".format(
                                    type_, dst, pattern, src
                                ),
                                YELLOW,
                            )
                        )
                        task_to_do = True
            if not managed and os.path.exists(dst):
                print(colorize("The destination '{}' already exists, ignoring.".format(dst), YELLOW))
            elif not managed:
                print("Move the {} '{}' to '{}'.".format(type_, src, dst))
                if "version" in element:
                    print("Needed from version {}.".format(element["version"]))
                if os.path.dirname(dst) != "":
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    check_call(["git", "mv", src, dst])
                except Exception as exception:
                    print("[Warning] Git move error: {}.".format(exception))
                    os.rename(src, dst)
        return task_to_do

    @Step(6)
    def step6(self, step):
        self.files_to_get(step)
        self.run_step(step + 1)

    def is_managed(self, file_, files_to_get=False):
        default_project_file = self.get_upgrade("default_project_file")

        # Managed means managed by the application owner, not the c2cupgrade
        managed = False
        if (
            not files_to_get
            or os.path.exists(file_)
            or not check_git_status_output(["CONST_create_template/" + file_]).startswith("A  ")
        ):
            for pattern in default_project_file["include"]:
                if re.match(pattern + "$", file_):
                    print("File '{}' included by migration config pattern '{}'.".format(file_, pattern))
                    managed = True
                    break
            if managed:
                for pattern in default_project_file["exclude"]:
                    if re.match(pattern + "$", file_):
                        print("File '{}' excluded by migration config pattern '{}'.".format(file_, pattern))
                        print("managed", file_, pattern)
                        managed = False
                        break
        else:
            print("New file '{}'.".format(file_))

        if not managed and not os.path.exists(file_):
            for pattern in self.get_upgrade("extra"):
                if re.match(pattern + "$", file_):
                    print("File '{}' is an extra by migration config pattern '{}'.".format(file_, pattern))
                    managed = True

        if not managed:
            for files in self.project["managed_files"]:
                if isinstance(files, str):
                    pattern = files
                else:
                    pattern = files["pattern"]
                if re.match(pattern + "$", file_):
                    print(
                        "File '{}' included by project config pattern `managed_files` '{}'.".format(
                            file_, pattern
                        )
                    )
                    print("managed", file_, pattern)
                    managed = True
                    break
        if managed:
            for pattern in self.project.get("unmanaged_files", []):
                if re.match(pattern + "$", file_):
                    print(
                        "File '{}' excluded by project config pattern `unmanaged_files` '{}'.".format(
                            file_, pattern
                        )
                    )
                    managed = False
                    break

        return managed

    def files_to_get(self, step, pre=False):
        error = False
        for root, _, files in os.walk("CONST_create_template"):
            # fmt: off
            root = root[len("CONST_create_template/"):]
            # fmt: on
            for file_ in files:
                destination = os.path.join(root, file_)
                managed = self.is_managed(destination, True)
                source = os.path.join("CONST_create_template", destination)
                if not managed and (not os.path.exists(destination) or not filecmp.cmp(source, destination)):
                    print(colorize("Get the file '{}' from the create template.".format(destination), GREEN))
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
                    print("The file '{}' is managed by the project.".format(destination))
                elif os.path.exists(destination) and filecmp.cmp(source, destination):
                    print("The file '{}' does not change.".format(destination))
                else:
                    print("Unknown stat for the file '{}'.".format(destination))
                    sys.exit(2)
        return error

    @Step(7)
    def step7(self, step):
        with open("changelog.diff", "w") as diff_file:
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

    def get_modified(self, status_path):
        status = check_git_status_output([status_path])
        status = [s for s in status.split("\n") if len(s) > 3]
        status = [s[3:] for s in status if s[:3].strip() == "M"]
        for pattern in self.get_upgrade("no_diff"):
            matcher = re.compile("CONST_create_template/{}$".format(pattern))
            status = [s for s in status if not matcher.match(s)]
        # fmt: off
        status = [s for s in status if os.path.exists(s[len("CONST_create_template/"):])]
        status = [s for s in status if not filecmp.cmp(s, s[len("CONST_create_template/"):])]
        # fmt: on
        return status

    @Step(8)
    def step8(self, step):
        if os.path.isfile("changelog.diff"):
            os.unlink("changelog.diff")

        status = self.get_modified(
            "CONST_create_template/geoportal/{}_geoportal/static-ngeo".format(self.project["project_package"])
        )

        with open("ngeo.diff", "w") as diff_file:
            if status:
                check_call(
                    ["git", "diff", "--relative=CONST_create_template", "--staged", "--"] + status,
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

    @Step(9)
    def step9(self, step):
        if os.path.isfile("ngeo.diff"):
            os.unlink("ngeo.diff")

        status = self.get_modified("CONST_create_template")
        status = [
            s
            for s in status
            if not s.startswith(
                "CONST_create_template/geoportal/{}_geoportal/static-ngeo/".format(
                    self.project["project_package"]
                )
            )
        ]

        if status:
            with open("create.diff", "w") as diff_file:
                if status:
                    check_call(
                        ["git", "diff", "--relative=CONST_create_template", "--staged", "--"] + status,
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

    @Step(10)
    def step10(self, step):
        if os.path.isfile("create.diff"):
            os.unlink("create.diff")

        message = [
            "The upgrade is nearly done, now you should:",
            "- Build your application with ./upgrade --finalize [build arguments]",
            "- Test your application on '{}'.".format(self.project.get("application_url", "... missing ...")),
        ]

        if os.path.isfile(".upgrade.yaml"):
            os.unlink(".upgrade.yaml")
        with open(".UPGRADE_SUCCESS", "w"):
            pass
        self.print_step(step + 1, message="\n".join(message))

    @Step(11, file_marker=False)
    def step11(self, step):
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
                "(If you want to fix it later you can pass to the next step):",
            )
            sys.exit(1)

    @Step(12, file_marker=False)
    def step12(self, step):
        # Required to remove from the Git stage the ignored file when we lunch the step again
        check_call(["git", "reset", "--mixed"])

        check_call(["git", "add", "-A"])
        check_call(["git", "status"])

        self.print_step(
            step + 1,
            message="We will commit all the above files!\n"
            "If there are some files which should not be committed, then you should "
            "add them into the `.gitignore` file and launch upgrade {} again.".format(step),
            prompt="Then to commit your changes type:",
        )

    @Step(13, file_marker=False)
    def step13(self, _):
        if os.path.isfile(".UPGRADE_INSTRUCTIONS"):
            os.unlink(".UPGRADE_INSTRUCTIONS")
        check_call(
            [
                "git",
                "commit",
                "--message=Upgrade to GeoMapFish {}".format(
                    pkg_resources.get_distribution("c2cgeoportal_commons").version
                ),
            ]
        )

        print("")
        print(self.color_bar)
        print("")
        print(colorize("Congratulations, your upgrade was successful.", GREEN))
        print("")
        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
        print("Now all your files are committed; you should do a git push:")
        print("git push {0!s} {1!s}.".format(self.options.git_remote, branch))


def check_git_status_output(args=None):
    return check_output(["git", "status", "--short"] + (args if args is not None else [])).decode("utf-8")


if __name__ == "__main__":
    main()
