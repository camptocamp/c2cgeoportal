# -*- coding: utf-8 -*-

# Copyright (c) 2014-2017, Camptocamp SA
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


import os
import re
import sys
import argparse
import httplib2
import yaml
import shutil
import pkg_resources
import subprocess
import filecmp
from subprocess import check_call, check_output
from argparse import ArgumentParser
from alembic.config import Config
from alembic import command
from c2cgeoportal_geoportal.lib.bashcolor import colorize, GREEN, YELLOW, RED

REQUIRED_TEMPLATE_KEYS = ["package", "srid", "extent"]
TEMPLATE_EXAMPLE = {
    "package": "${package}",
    "srid": "${srid}",
    "extent": "489246, 78873, 837119, 296543",
}
DIFF_NOTICE = "The changes visible on `a/CONST_create_template/<file>` should be done on `<file>`.\n" \
    "An advise to be more effective: in most cases it concerns a file that you never customize, " \
    "or a file that you have heavily customized, then respectively copy the new file from " \
    "`CONST_create_template` (`cp CONST_create_template/<file> <file>`), respectively ignore " \
    "the changes."


def main():
    """
    tool used to do the application upgrade
    """

    parser = _fill_arguments()
    options = parser.parse_args()
    if options.force_docker:
        options.nondocker = False
    if options.new_makefile is None:
        options.new_makefile = options.makefile

    print("Start the upgrade with the options:")
    if options.windows:
        print("- windows")
    if options.nondocker:
        print("- nondocker")
    print("- git_remote=" + options.git_remote)
    if options.use_makefile:
        print("- use_makefile")
    print("- makefile=" + options.makefile)
    print("- new_makefile=" + options.new_makefile)
    sys.stdout.flush()

    c2cupgradetool = C2cUpgradeTool(options)
    c2cupgradetool.upgrade()


def _fill_arguments():
    parser = ArgumentParser()
    parser.add_argument(
        "--windows",
        action="store_true",
        help="Use the windows c2cgeoportal package",
    )
    parser.add_argument(
        "--nondocker",
        action="store_true",
        help="Use the nondocker upgrade",
    )
    parser.add_argument(
        "--force-docker",
        action="store_true",
        help="Use the desable the nondocker upgrade",
    )
    parser.add_argument(
        "--git-remote",
        metavar="GITREMOTE",
        help="Specify the remote branch",
        default="origin",
    )
    parser.add_argument(
        "--makefile", help="The makefile used to build", default="Makefile",
    )
    parser.add_argument(
        "--new-makefile", help="The makefile used to override the makefile",
    )
    parser.add_argument(
        "--use-makefile", action="store_true", help="c2cupgrade is running form a makefile",
    )
    parser.add_argument(
        "--step", type=int, help=argparse.SUPPRESS, default=0
    )

    return parser


class InteruptedException(Exception):
    pass


class Step:
    def __init__(self, step_number):
        self.step_number = step_number

    def __call__(self, current_step):
        def decorate(c2cupgradetool, *args, **kwargs):
            try:
                if os.path.isfile(".UPGRADE{}".format(self.step_number - 1)):
                    os.unlink(".UPGRADE{}".format(self.step_number - 1))
                if self.step_number not in [0, 12]:
                    with open(".UPGRADE{}".format(self.step_number), "w"):
                        pass
                print("Start step {}.".format(self.step_number))
                sys.stdout.flush()
                current_step(c2cupgradetool, self.step_number, *args, **kwargs)
            except subprocess.CalledProcessError as e:
                c2cupgradetool.print_step(
                    self.step_number, error=True,
                    message="The command '{}' returns the error code {}.".format(e.cmd, e.returncode),
                    prompt="Fix it and run it again:"
                )
                exit(1)
            except InteruptedException as e:
                c2cupgradetool.print_step(
                    self.step_number, error=True,
                    message="It was an error: {}.".format(e),
                    prompt="Fix it and run it again:"
                )
                exit(1)
        return decorate


class C2cUpgradeTool:

    color_bar = colorize("================================================================", GREEN)
    project = None

    def __init__(self, options):
        self.options = options
        self.project = self.get_project()

    @staticmethod
    def get_project():
        if not os.path.isfile("project.yaml"):
            print(colorize("Unable to find the required 'project.yaml' file.", RED))
            exit(1)

        with open("project.yaml", "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def get_upgrade(section):
        if not os.path.isfile(".upgrade.yaml"):
            print(colorize("Unable to find the required '.upgrade.yaml' file.", RED))
            exit(1)

        with open(".upgrade.yaml", "r") as f:
            return yaml.safe_load(f)[section]

    def print_step(self, step, error=False, message=None, prompt="To continue type:"):
        print("")
        print(self.color_bar)
        if message is not None:
            print(colorize(message, RED if error else YELLOW))
        if step >= 0:
            print(colorize(prompt, GREEN))
            if self.options.use_makefile:
                args = " --makefile={}".format(self.options.makefile) \
                    if self.options.makefile != "Makefile" else ""
                print(colorize("./docker-run make{} upgrade{}".format(
                    args, step if step != 0 else "",
                ), GREEN))
            else:
                cmd = "./docker-run --image=camptocamp/geomapfish-build --version={} c2cupgrade ".format(
                    pkg_resources.get_distribution("c2cgeoportal_commons").version)
                if self.options.windows:
                    cmd += "--windows "
                if self.options.nondocker:
                    cmd += "--nondocker "
                if self.options.force_docker:
                    cmd += "--force-docker "
                if self.options.git_remote != "origin":
                    cmd += "--git-remote={} ".format(self.options.git_remote)
                if self.options.makefile != "Makefile":
                    cmd += "--makefile={} ".format(self.options.makefile)
                if self.options.new_makefile is not None:
                    cmd += "--new-makefile={} ".format(self.options.new_makefile)
                if step != 0:
                    cmd += "--step={}".format(step)
                print(colorize(cmd, GREEN))

    def run_step(self, step):
        getattr(self, "step{}".format(step))()

    def test_checkers(self):
        http = httplib2.Http()
        for check_type in ("", "type=all"):
            resp, _ = http.request(
                "http://localhost{}{}".format(self.project["checker_path"], check_type),
                method="GET",
                headers={
                    "Host": self.project["host"]
                }
            )
            if resp.status < 200 or resp.status >= 300:
                return False, "\n".join([
                    "Checker error:",
                    "Open `http://{}{}{}` for more information."
                ]).format(
                    self.project["host"], self.project["checker_path"], check_type
                )

        return True, None

    def upgrade(self):
        self.run_step(self.options.step)

    @Step(0)
    def step0(self, step):
        project_template_keys = list(self.project.get("template_vars").keys())
        messages = []
        for required in REQUIRED_TEMPLATE_KEYS:
            if required not in project_template_keys:
                messages.append(
                    "The element '{}' is missing in the 'template_vars' of "
                    "the file 'project.yaml.mako', you should for example: {}: {}.".format(
                        required, required, TEMPLATE_EXAMPLE.get('required', '')
                    )
                )
        if len(messages) > 0:
            self.print_step(
                step, error=True, message="\n".join(messages),
                prompt="Fix it and run again the upgrade:")
            exit(1)

        if check_output(["git", "status", "--short"]).decode("utf-8") == "":
            self.run_step(step + 1)
        else:
            check_call(["git", "status"])
            self.print_step(
                step + 1, message="Here is the output of 'git status'. Please make sure to commit all your "
                "changes before going further. All uncommited changes will be lost."
            )

    @Step(1)
    def step1(self, step):
        check_call(["git", "reset", "--hard"])
        check_call(["git", "clean", "--force", "-d"])

        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
        # remove all no more existing branches
        check_call(["git", "fetch", "origin", "--prune"])
        branches = check_output(["git", "branch", "--all"]).decode("utf-8").split("\n")
        if "  remotes/origin/{0!s}".format(branch) in branches:
            try:
                check_call(["git", "pull", "--rebase", self.options.git_remote, branch])
            except subprocess.CalledProcessError:
                self.print_step(
                    step, error=True, message="The pull (rebase) failed.",
                    prompt="Please solve the rebase and run it again:")
                exit(1)

        if len(check_output(["git", "status", "-z"]).decode("utf-8").strip()) != 0:
            self.print_step(
                step, error=True, message="The pull is not fast forward.",
                prompt="Please solve the rebase and run it again:")
            exit(1)

        self.run_step(step + 1)

    @Step(2)
    def step2(self, step):
        if not os.path.exists("CONST_create_template/geoportal"):
            for source, destination in [
                ("testDB", "testdb"),
                ("testdb/Dockerfile.mako", "testdb/Dockerfile"),
                ("vars_{{package}}.yaml", "vars.yaml"),
                ("{{package}}.mk", "Makefile"),
                ("Dockerfile", "geoportal/Dockerfile.mako"),
                ("docker-compose.yml.mako", "docker-compose.yaml.mako"),
                (".dockerignore", "geoportal/.dockerignore"),
                ("jsbuild", "geoportal/jsbuild"),
                ("production.ini.mako", "geoportal/production.ini.mako"),
                ("setup.py", "geoportal/setup.py"),
                ("testgeomapfish/models.py", "commons/testgeomapfish_commons/models.py"),
                ("testgeomapfish", "geoportal/testgeomapfish_geoportal"),
            ]:
                if os.path.exists(source):
                    if os.path.dirname(destination) != "":
                        os.makedirs(os.path.dirname(destination), exist_ok=True)
                    check_call(["git", "mv", source, destination])
            check_call(["git", "commit", "--message=Do the moves in CONST_create_template"])
        self.run_step(step + 1)

    @Step(3)
    def step3(self, step):
        if os.path.exists("CONST_create_template"):
            shutil.rmtree("CONST_create_template")

        project_path = os.path.join("/tmp", self.project["project_folder"])
        check_call(["ln", "-s", "/src", project_path])
        check_call([
            "pcreate", "--ignore-conflicting-name", "--overwrite",
            "--scaffold=c2cgeoportal_update", project_path
        ])
        if self.options.nondocker:
            check_call([
                "pcreate", "--ignore-conflicting-name", "--overwrite",
                "--scaffold=c2cgeoportal_nondockerupdate", project_path
            ])
        os.remove(project_path)

        check_call(["make", "--makefile=" + self.options.makefile, "clean-all"])
        self.run_step(step + 1)

    @Step(4)
    def step4(self, step):
        error = False

        print("Files to remove")
        error |= self.files_to_remove(pre=True)
        print("Files to move")
        error |= self.files_to_move(pre=True)
        print("Files to get")
        error |= self.files_to_get(pre=True)

        if error:
            self.print_step(
                step, error=True, message="There was some error on your project configuration, see above",
                prompt="Fix it and run it again:"
            )
            exit(1)
        else:
            if "managed_files" not in self.project:
                self.print_step(
                    step,
                    message="In the new version we will also manage almost all the create "
                    "template files.\n"
                    "By default following regex pattern will not be replaced:\n{}"
                    "Than you should fill the 'managed_files' in you 'project.yaml' file with at least "
                    "`[]`.".format("\n".join([
                        "- " + e for e in self.project.get('unmanaged_files', [])
                    ])),
                    prompt="Fill it and run it again:"
                )
            else:
                self.options.use_makefile = True
                self.options.makefile = self.options.new_makefile
                self.run_step(step + 1)

    @Step(5)
    def step5(self, step):
        self.files_to_remove()
        self.run_step(step + 1)

    def files_to_remove(self, pre=False):
        error = False
        for element in self.get_upgrade("files_to_remove"):
            file_ = element["file"]
            if os.path.exists(file_):
                managed = False
                for pattern in self.project["managed_files"]:
                    if re.match(pattern + '$', file_):
                        print(colorize(
                            "The file '{}' is no more use but not delete "
                            "because he is in the managed_files as '{}'.".format(file_, pattern),
                            RED
                        ))
                        error = True
                        managed = True
                if not managed and not pre:
                    print(colorize("The file '{}' is removed.".format(file_), GREEN))
                    if "version" in element and "from" in element:
                        print("Was used in version {}, to be removed from version {}.".format(
                            element["from"], element["version"]
                        ))
                    if os.path.isdir(file_):
                        shutil.rmtree(file_)
                    else:
                        os.remove(file_)
        return error

    @Step(6)
    def step6(self, step):
        self.files_to_move()
        self.run_step(step + 1)

    def files_to_move(self, pre=False):
        error = False
        for element in self.get_upgrade("files_to_move"):
            src = element["from"]
            dst = element["to"]
            if os.path.exists(src):
                type_ = "directory" if os.path.isdir(src) else "file"
                managed = False
                for pattern in self.project["managed_files"]:
                    if re.match(pattern + '$', src):
                        print(colorize(
                            "The {} '{}' is present in the managed_files as '{}' but he will move.".format(
                                type_, src, pattern),
                            RED
                        ))
                        error = True
                        managed = True
                        break
                    if re.match(pattern + '$', dst):
                        print(colorize(
                            "The {} '{}' is present in the managed_files as '{}' but he will move.".format(
                                type_, dst, pattern),
                            RED
                        ))
                        error = True
                        managed = True
                        break
                if not managed and os.path.exists(dst):
                    print(colorize(
                        "The destination '{}' already exists.".format(dst),
                        RED
                    ))
                    error = True
                    if not pre:
                        raise InteruptedException("The destination '{}' already exists.".format(dst))
                if not managed and not pre:
                    print(colorize("Move the {} '{}' to '{}'.".format(type_, src, dst), GREEN))
                    if "version" in element:
                        print("Needed from version {}.".format(element["version"]))
                    if os.path.dirname(dst) != "":
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                    os.rename(src, dst)
        return error

    @Step(7)
    def step7(self, step):
        self.files_to_get()
        self.run_step(step + 1)

    def files_to_get(self, pre=False):
        error = False
        for root, _, files in os.walk("CONST_create_template"):
            root = root[len("CONST_create_template/"):]
            for file_ in files:
                destination = os.path.join(root, file_)
                managed = False
                for pattern in self.project["managed_files"] + self.get_upgrade("default_project_file"):
                    if re.match(pattern + '$', destination):
                        managed = True
                        for unpattern in self.project.get("unmanaged_files", []):
                            if re.match(unpattern + '$', destination):
                                managed = False
                                break
                        break
                source = os.path.join("CONST_create_template", destination)
                if not managed and (not os.path.exists(destination) or not filecmp.cmp(source, destination)):
                    if not pre:
                        print(colorize(
                            "Get the file '{}' from the create template.".format(destination), GREEN
                        ))
                        if os.path.dirname(destination) != "":
                            os.makedirs(os.path.dirname(destination), exist_ok=True)
                        shutil.copyfile(source, destination)
                        shutil.copymode(source, destination)
        return error

    @Step(8)
    def step8(self, step):
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
                "file (listed in the `changelog.diff` file)."
            )

    @Step(9)
    def step9(self, step):
        if os.path.isfile("changelog.diff"):
            os.unlink("changelog.diff")

        status = check_output(["git", "status", "--short", "CONST_nondocker_CHANGELOG.txt"]).decode("utf-8")
        if status.strip() == "?? CONST_nondocker_CHANGELOG.txt":
            check_call(["cp", "CONST_nondocker_CHANGELOG.txt", "nondocker-changelog.diff"])
        else:
            with open("nondocker-changelog.diff", "w") as diff_file:
                check_call(["git", "diff", "--", "CONST_nondocker_CHANGELOG.txt"], stdout=diff_file)

        if os.path.getsize("nondocker-changelog.diff") == 0:
            self.run_step(step + 1)
        else:
            self.print_step(
                step + 1,
                message="Apply the manual migration steps based on what is in the "
                "CONST_nondocker_CHANGELOG.txt file (listed in the `nondocker-changelog.diff` file)."
            )

    @Step(10)
    def step10(self, step):
        if os.path.isfile("nondocker-changelog.diff"):
            os.unlink("nondocker-changelog.diff")

        with open("ngeo.diff", "w") as diff_file:
            check_call([
                "git", "diff", "--",
                "CONST_create_template/geoportal/{}_geoportal/templates".format(
                    self.project["project_package"]),
                "CONST_create_template/geoportal/{}_geoportal/static-ngeo".format(
                    self.project["project_package"]),
            ], stdout=diff_file)

        if os.path.getsize("ngeo.diff") == 0:
            self.run_step(step + 1)
        else:
            self.print_step(
                step + 1,
                message="Manually apply the ngeo application changes as shown in the `ngeo.diff` file.\n" +
                DIFF_NOTICE
            )

    @Step(11)
    def step11(self, step):
        if os.path.isfile("ngeo.diff"):
            os.unlink("ngeo.diff")

        status = check_output(["git", "status", "--short", "CONST_create_template"]).decode("utf-8")
        status = [s for s in status.split("\n") if len(s) > 3]
        status = [s[3:] for s in status if s.startswith(" M ")]
        status = [s for s in status if not s.startswith(
            "CONST_create_template/{}/templates/".format(self.project["project_package"]),
        )]
        status = [s for s in status if not s.startswith(
            "CONST_create_template/{}/static-ngeo/".format(self.project["project_package"]),
        )]
        matcher = re.compile(r"CONST_create_tremplate.*/CONST_.+")
        status = [s for s in status if not matcher.match(s)]
        status = [s for s in status if not filecmp.cmp(s, s[len("CONST_create_template/"):])]

        if len(status) > 0:
            with open("create.diff", "w") as diff_file:
                check_call(["git", "diff", "--"] + status, stdout=diff_file)

            if os.path.getsize("create.diff") == 0:
                self.run_step(step + 1)
            else:
                self.print_step(
                    step + 1, message="This is an optional step but it helps to have a standard project.\n"
                    "The `create.diff` file is a recommendation of the changes that you should apply "
                    "to your project.\n" + DIFF_NOTICE
                )
        else:
            self.run_step(step + 1)

    @Step(12)
    def step12(self, step):
        if os.path.isfile("create.diff"):
            os.unlink("create.diff")

        check_call(["make", "--makefile=" + self.options.new_makefile, "build"])

        if self.options.nondocker:
            command.upgrade(Config("alembic.ini", ini_section="main"), "head")
            command.upgrade(Config("alembic.ini", ini_section="static"), "head")

            message = [
                "The upgrade is nearly done, now you should:",
                "- Test your application."
            ]
        else:
            message = [
                "The upgrade is nearly done, now you should:",
                "- run `docker-compose up`",
                "- Test your application on 'http://localhost:8480/desktop'."
            ]

        if self.options.windows:
            message.append(
                "You are running on Windows, please restart your Apache server,"
                "because we can not do that automatically."
            )

        if os.path.isfile(".upgrade.yaml"):
            os.unlink(".upgrade.yaml")
        with open(".UPGRADE_SUCCESS", "w"):
            pass
        self.print_step(step + 1, message="\n".join(message))

    @Step(13)
    def step13(self, step):
        if os.path.isfile(".UPGRADE_SUCCESS"):
            os.unlink(".UPGRADE_SUCCESS")
        ok, message = self.test_checkers()
        if not ok:
            self.print_step(step, error=True, message=message, prompt="Correct the checker, the it again:")
            exit(1)

        # Required to remove from the Git stage the ignored file when we lunch the step again
        check_call(["git", "reset", "--mixed"])

        check_call(["git", "add", "-A"])
        check_call(["git", "status"])

        self.print_step(
            step + 1, message="We will commit all the above files!\n"
            "If there are some files which should not be committed, then you should "
            "add them into the `.gitignore` file and launch upgrade5 again.",
            prompt="Then to commit your changes type:")

    @Step(14)
    def step14(self, _):
        check_call(["git", "commit", "--message=Upgrade to GeoMapFish {}".format(
            pkg_resources.get_distribution("c2cgeoportal_commons").version
        )])

        print("")
        print(self.color_bar)
        print("")
        print(colorize("Congratulations your upgrade is a success.", GREEN))
        print("")
        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
        print("Now all your files will be committed, you should do a git push:")
        print("git push {0!s} {1!s}.".format(
            self.options.git_remote, branch
        ))


if __name__ == "__main__":
    main()
