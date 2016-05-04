# -*- coding: utf-8 -*-

# Copyright (c) 2014-2016, Camptocamp SA
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
from os import path, unlink
import re
import sys
import shutil
import argparse
import httplib2
import yaml
from subprocess import check_call, CalledProcessError
from argparse import ArgumentParser
from alembic.config import Config
from alembic import command
from c2cgeoportal.lib.bashcolor import colorize, GREEN, YELLOW, RED

try:
    from subprocess import check_output
except ImportError:
    from subprocess import Popen, PIPE

    def check_output(cmd, cwd=None, stdin=None, stderr=None, shell=False):  # noqa
        """Backwards compatible check_output"""
        p = Popen(cmd, cwd=cwd, stdin=stdin, stderr=stderr, shell=shell, stdout=PIPE)
        out, err = p.communicate()
        return out

VERSION_RE = "^[0-9]+\.[0-9]+\..+$"
REQUIRED_TEMPLATE_KEYS = ["package", "srid", "extent", "apache_vhost"]
TEMPLATE_EXAMPLE = {
    "package": "${package}",
    "srid": "${srid}",
    "extent": "489246, 78873, 837119, 296543",
    "apache_vhost": "<apache_vhost>",
}


def main():
    """
    tool used to help th use in the user tash
    """

    usage = """usage: {prog} [command] [options]

Available commands:

""" + colorize("help", GREEN) + """: show this page
""" + colorize("upgrade", GREEN) + """: upgrade the application to a new version
""" + colorize("deploy", GREEN) + """: deploy the application to a server

To have some help on a command type:
{prog} help [command]""".format(prog=sys.argv[0])

    if len(sys.argv) <= 1:
        print(usage)
        exit()

    if sys.argv[1] == "help":
        if len(sys.argv) > 2:
            parser = _fill_arguments(sys.argv[2])
            parser.print_help()
        else:
            print(usage)
        exit()

    parser = _fill_arguments(sys.argv[1])
    options = parser.parse_args(sys.argv[2:])

    c2ctool = C2cTool(options)
    if sys.argv[1] == "upgrade":
        c2ctool.upgrade()
    elif sys.argv[1] == "deploy":
        c2ctool.deploy()
    else:
        print("Unknown command")


def _fill_arguments(command):
    parser = ArgumentParser(prog="%s %s" % (sys.argv[0], command), add_help=False)
    parser.add_argument(
        "--no-cleanall",
        help="Run clean instead of cleanall",
        default="cleanall",
        action="store_const",
        const="clean",
        dest="clean",
    )
    parser.add_argument(
        "--windows",
        action="store_true",
        help="Use the windows c2cgeoportal package",
    )
    parser.add_argument(
        "--git-remote",
        metavar="GITREMOTE",
        help="Specify the remote branch",
        default="origin",
    )
    parser.add_argument(
        "--index-url",
        help="no more used",
    )
    parser.add_argument(
        "--c2cgeoportal-url",
        help="no more used",
    )

    if command == "help":
        parser.add_argument(
            "command", metavar="COMMAND", help="The command"
        )
    elif command == "upgrade":
        parser.add_argument(
            "file", metavar="MAKEFILE", help="The makefile used to build", default=None
        )
        parser.add_argument(
            "--step", type=int, help=argparse.SUPPRESS, default=0
        )
        parser.add_argument(
            "version", metavar="VERSION", help="Upgrade to version"
        )
    elif command == "deploy":
        parser.add_argument(
            "host", metavar="HOST", help="The destination host"
        )
        parser.add_argument(
            "--components",
            help="Restrict component to update. [databases,files,code]. default to all",
            default=None
        )
    else:
        print("Unknown command")
        exit()

    return parser


class C2cTool:

    color_bar = colorize("================================================================", GREEN)

    def print_step(self, step, intro="To continue type:"):
        print(colorize(intro, YELLOW))
        print(colorize("make -f {} upgrade{}", GREEN).format(
            self.options.file if self.options.file is not None else "<user.mk>",
            step if step != 0 else "",
        ))

    def get_project(self):
        if not path.isfile("project.yaml"):
            print("Unable to find the required 'project.yaml' file.")
            exit(1)

        with open("project.yaml", "r") as f:
            return yaml.load(f)

    def test_checkers(self):
        http = httplib2.Http()
        for check_type in ("", "type=all"):
            resp, content = http.request(
                "http://localhost%s%s" % (self.project["checker_path"], check_type),
                method="GET",
                headers={
                    "Host": self.project["host"]
                }
            )
            if resp.status < 200 or resp.status >= 300:
                print(self.color_bar)
                print("Checker error:")
                print("Open `http://%s%s%s` for more informations." % (
                    self.project["host"], self.project["checker_path"], check_type
                ))
                return False
        return True

    def __init__(self, options):
        self.options = options
        self.project = self.get_project()

    def upgrade(self):
        self.venv_bin = ".build/venv/bin"
        if self.options.windows:
            self.options.clean = "clean"
            self.venv_bin = ".build/venv/Scripts"

        if self.options.step == 0:
            self.step0()
        elif self.options.step == 1:
            self.step1()
        elif self.options.step == 2:
            self.step2()
        elif self.options.step == 3:
            self.step3()
        elif self.options.step == 4:
            self.step4()

    def step0(self):
        project_template_keys = self.project.get("template_vars").keys()
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
            print("")
            print(self.color_bar)
            print(colorize("\n".join(messages), RED))
            print("")
            self.print_step(0, intro="Fix it and run again the upgrade:")
            exit(1)

        if re.match(VERSION_RE, self.options.version) is not None:
            http = httplib2.Http()
            headers, _ = http.request(
                "https://github.com/camptocamp/CGXP/tree/%s" %
                self.options.version, "HEAD"
            )
            if headers.status != 200:
                print("")
                print(self.color_bar)
                print("This CGXP tag does not exist, the upgrade is impossible...")
                exit(1)

            url = (
                "http://raw.github.com/camptocamp/c2cgeoportal/%s/"
                "c2cgeoportal/scaffolds/update/CONST_versions.txt" % self.options.version
            )
            headers, _ = http.request(url)
            if headers.status != 200:
                print("")
                print(self.color_bar)
                print("Failed downloading the c2cgeoportal CONST_versions.txt file form URL:")
                print(url)
                print("The upgrade is impossible")
                exit(1)

        if path.split(path.realpath("."))[1] != self.project["project_folder"]:
            print("")
            print(self.color_bar)
            print("Your project isn't in the right folder!")
            print("It should be in folder '%s' instead of folder '%s'." % (
                self.project["project_folder"], path.split(path.realpath("."))[1]
            ))
            print("")
            self.print_step(0, intro="Fix it and lunch again the upgrade:")
            exit(1)

        check_call(["git", "status"])
        print("")
        print(self.color_bar)
        print(
            "Here is the output of 'git status'. Please make sure to commit all your changes "
            "before going further. All uncommited changes will be lost."
        )
        self.print_step(1)

    def step1(self):
        notes = []

        check_call(["git", "reset", "--hard"])
        check_call(["git", "clean", "--force", "-d"])
        check_call(["git", "submodule", "foreach", "--recursive", "git", "reset", "--hard"])
        check_call(["git", "submodule", "foreach", "--recursive", "git", "clean", "--force", "-d"])

        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
        # remove all no more existing branches
        check_call(["git", "fetch", "origin", "--prune"])
        branches = check_output(["git", "branch", "--all"]).split("\n")
        if "  remotes/origin/%s" % branch in branches:
            try:
                check_call(["git", "pull", "--rebase", self.options.git_remote, branch])
            except CalledProcessError:
                print(self.color_bar)
                print("")
                print(colorize("The pull (rebase) failed.", RED))
                print("")
                self.print_step(1, intro="Please solve the rebase and run the step 1 again:")
                exit(1)

        check_call(["git", "submodule", "sync"])
        check_call(["git", "submodule", "update", "--init"])
        check_call(["git", "submodule", "foreach", "git", "submodule", "sync"])
        check_call(["git", "submodule", "foreach", "git", "submodule", "update", "--init"])

        if len(check_output(["git", "status", "-z"]).strip()) != 0:
            print(self.color_bar)
            print("")
            print(colorize("The pull isn't fast forward.", RED))
            print("")
            self.print_step(1, intro="Please solve the rebase and run the step 1 again:")
            exit(1)

        check_call(["git", "submodule", "foreach", "git", "fetch", "origin"])
        if "TRAVIS_FOLDER" in os.environ:
            pass
        elif self.options.version == "master":
            check_call([
                "git", "submodule", "foreach", "git", "reset", "--hard",
                "origin/%s" % self.options.version, "--"
            ])
        elif re.match(VERSION_RE, self.options.version) is not None:
            check_call([
                "git", "submodule", "foreach", "git", "reset", "--hard",
                self.options.version, "--"
            ])
        else:
            notes.append(
                "We can't define the cgxp revision, than you should manually do:\n"
                "git submodule foreach git reset --hard <revision>"
            )

        check_call(["git", "submodule", "foreach", "git", "submodule", "sync"])
        check_call(["git", "submodule", "foreach", "git", "submodule", "update", "--init"])

        if not self.options.windows:
            check_call(["make", "-f", self.options.file, ".build/requirements.timestamp"])
            pip_cmd = ["%s/pip" % self.venv_bin, "install"]
            if self.options.version == "master":
                check_call(["%s/pip" % self.venv_bin, "uninstall", "--yes", "c2cgeoportal"])
                pip_cmd += ["--pre", "c2cgeoportal"]
            else:
                pip_cmd += ["c2cgeoportal==%s" % (self.options.version)]
            check_call(pip_cmd)

        check_call([
            "%s/pcreate" % self.venv_bin, "--ignore-conflicting-name", "--overwrite",
            "--scaffold=c2cgeoportal_update", "../%s" % self.project["project_folder"]
        ])
        pcreate_cmd = [
            "%s/pcreate" % self.venv_bin, "--ignore-conflicting-name",
            "--scaffold=c2cgeoportal_create", "/tmp/%s" % self.project["project_folder"],
        ]
        for name, value in self.project["template_vars"].items():
            if isinstance(value, basestring):
                value = value.encode('utf-8')
            pcreate_cmd.append("{}={}".format(name, value))
        check_call(pcreate_cmd)
        check_call(["make", "-f", self.options.file, self.options.clean])

        diff_file = open("changelog.diff", "w")
        check_call(["git", "diff", "CONST_CHANGELOG.txt"], stdout=diff_file)
        diff_file.close()

        check_call(["make", "-f", self.options.file, "update-node-modules"])
        check_call(["make", "-f", self.options.file, ".build/requirements.timestamp"])

        print("")
        print(self.color_bar)
        print("\n".join(notes))
        print(
            "Apply the manual migration steps based on what is in the CONST_CHANGELOG.txt file"
            " (listed in the `changelog.diff` file)."
        )
        self.print_step(2)

    def step2(self):
        if self.options.file is None:
            print("")
            print(self.color_bar)
            print("The makefile is missing")
            print("")
            self.print_step(2, intro="Fix it and run again the step 2:")
            exit(1)

        if path.isfile("changelog.diff"):
            unlink("changelog.diff")

        check_call(["make", "-f", self.options.file, "build"])

        command.upgrade(Config("alembic.ini"), "head")
        command.upgrade(Config("alembic_static.ini"), "head")

        if not self.options.windows:
            check_call(self.project.get("cmds", {}).get(
                "apache_graceful",
                ["sudo", "/usr/sbin/apache2ctl", "graceful"]
            ))

        print("")
        print(self.color_bar)
        print("The upgrade is nearly done, now you should:")
        print("- Test your application.")

        if self.options.windows:
            print("You are running on Windows, please restart your Apache server,")
            print("because we can not do that automatically.")

        self.print_step(3)

    def step3(self):
        if not self.test_checkers():
            print("")
            self.print_step(3, intro="Correct the checker, the step 3 again:")
            exit(1)

        if path.exists("/tmp/%s" % self.project["project_folder"]):
            shutil.rmtree("/tmp/%s" % self.project["project_folder"])

        # Required to remove from the Git stage the ignored file when we lunch the step again
        check_call(["git", "reset", "--mixed"])

        check_call(["git", "add", "-A"])
        if path.exists("%s/static/lib/cgxp" % self.project["project_package"]):
            check_call(["git", "add", "%s/static/lib/cgxp" % self.project["project_package"]])
        check_call(["git", "status"])

        print("")
        print(self.color_bar)
        print("We will commit all the above files!")
        print(
            "If there are some files which should not be commited, then you should "
            "add them into the `.gitignore` file and launch step 3 again."
        )

        self.print_step(4, intro="Then to commit your changes type:")

    def step4(self):
        check_call(["git", "commit", "-m", "Upgrade to GeoMapFish %s" % self.options.version])

        print("")
        print(self.color_bar)
        print("")
        print(colorize("Congratulations your upgrade is a success.", GREEN))
        print("")
        branch = check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()
        print("Now all your files will be commited, you should do a git push %s %s." % (
            self.options.git_remote, branch
        ))

    def deploy(self):
        if not self.test_checkers():
            print(colorize("Correct them and run again", RED))
            exit(1)

        check_call(["sudo", "-u", "deploy", "deploy", "-r", "deploy/deploy.cfg", self.options.host])
        check_call(["make", "-f", self.options.file, "build"])


if __name__ == "__main__":
    main()
