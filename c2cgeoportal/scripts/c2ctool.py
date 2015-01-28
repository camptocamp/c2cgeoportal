# -*- coding: utf-8 -*-

# Copyright (c) 2014-2015, Camptocamp SA
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


from os import environ, path, unlink
import sys
import shutil
import argparse
import httplib2
from yaml import load
from subprocess import check_call
from argparse import ArgumentParser
from alembic.config import Config
from alembic import command

try:
    from subprocess import check_output
except ImportError:
    from subprocess import Popen, PIPE

    def check_output(cmd, cwd=None, stdin=None, stderr=None, shell=False):  # noqa
        """Backwards compatible check_output"""
        p = Popen(cmd, cwd=cwd, stdin=stdin, stderr=stderr, shell=shell, stdout=PIPE)
        out, err = p.communicate()
        return out

BLACK = 0
RED = 1
GREEN = 2
YELLOW = 3
BLUE = 4
MAGENTA = 5
CYAN = 6
WHITE = 7


def _colorize(text, color):
    return "\x1b[01;3%im%s\x1b[0m" % (color, text)

_command_to_use = None
_color_bar = _colorize("=================================================================", GREEN)


def main():  # pragma: no cover
    """
    tool used to help th use in the user tash
    """

    usage = """usage: {prog} [command] [options]

Available commands:

""" + _colorize("help", GREEN) + """: show this page
""" + _colorize("update", GREEN) + """: update the application code
""" + _colorize("upgrade", GREEN) + """: upgrade the application to a new version
""" + _colorize("deploy", GREEN) + """: deploy the application to a server

To have some help on a command type:
{prog} help [command]""".format(prog=sys.argv[0])

    if len(sys.argv) <= 1:
        print usage
        exit()

    if sys.argv[1] == 'help':
        if len(sys.argv) > 2:
            parser = _fill_arguments(sys.argv[2])
            parser.print_help()
        else:
            print usage
        exit()

    parser = _fill_arguments(sys.argv[1])
    options = parser.parse_args(sys.argv[2:])

    global _command_to_use
    _command_to_use = environ['COMMAND_TO_USE'] if 'COMMAND_TO_USE' in environ else sys.argv[0]

    if sys.argv[1] == 'update':
        update(options)
    elif sys.argv[1] == 'upgrade':
        upgrade(options)
    elif sys.argv[1] == 'deploy':
        deploy(options)
    else:
        print "Unknown command"


def _fill_arguments(command):
    parser = ArgumentParser(prog="%s %s" % (sys.argv[0], command), add_help=False)
    if command == 'help':
        parser.add_argument(
            'command', metavar='COMMAND', help='The command'
        )
    elif command == 'update':
        parser.add_argument(
            'file', metavar='MAKEFILE', help='The makefile used to build'
        )
    elif command == 'upgrade':
        parser.add_argument(
            'file', metavar='MAKEFILE', help='The makefile used to build', default=None
        )
        parser.add_argument(
            '--step', type=int, help=argparse.SUPPRESS, default=0
        )
        parser.add_argument(
            'version', metavar='VERSION', help='Upgrade to version'
        )
    elif command == 'deploy':
        parser.add_argument(
            'host', metavar='HOST', help='The destination host'
        )
        parser.add_argument(
            '--components',
            help="Restrict component to update. [databases,files,code]. default to all",
            default=None
        )
    else:
        print "Unknown command"
        exit()

    return parser


def update(options):
    branch = check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
    print "Use branch %s." % branch
    check_call(['git', 'pull', '--rebase', 'origin', branch])
    if len(check_output(['git', 'status', '-z']).strip()) != 0:
        print _color_bar
        print _colorize("The pull isn't fast forward.", RED)
        print _colorize("Please solve the rebase and run it again.", YELLOW)
        exit(1)

    check_call(['git', 'submodule', 'sync'])
    check_call(['git', 'submodule', 'update', '--init'])
    check_call(['git', 'submodule', 'foreach', 'git', 'submodule', 'sync'])
    check_call(['git', 'submodule', 'foreach', 'git', 'submodule', 'update', '--init'])

    check_call(['make', '-f', options.file, 'build'])
    check_call(['sudo', '/usr/sbin/apache2ctl', 'graceful'])


def _print_step(options, step, intro="To continue type:"):
    global _command_to_use
    print intro
    print _colorize("%s upgrade %s %s --step %i", YELLOW) % (
        _command_to_use,
        options.file if options.file is not None else "<user.mk>",
        options.version, step
    )


def _get_project():
    if not path.isfile('project.yaml'):
        print "Unable to find the required 'project.yaml' file."
        exit(1)

    return load(file('project.yaml', 'r'))


def _test_checkers(project):
    http = httplib2.Http()
    for check_type in ["", "type=all"]:
        resp, content = http.request(
            "http://localhost%s%s" % (project['checker_path'], check_type),
            method='GET',
            headers={
                "Host": project['host']
            }
        )
        if resp.status < 200 or resp.status >= 300:
            print(_color_bar)
            print "Checker error:"
            print "Open `http://%s%s%s` for more informations." % (
                project['host'], project['checker_path'], check_type
            )
            return False
    return True


def upgrade(options):
    project = _get_project()

    if options.step == 0:
        if path.split(path.realpath('.'))[1] != project['project_folder']:
            print "Your project isn't in the right folder!"
            print "It should be in folder '%s' instead of folder '%s'." % (
                project['project_folder'], path.split(path.realpath('.'))[1]
            )

        check_call(['git', 'status'])
        print
        print _color_bar
        print "Here is the output of 'git status'. Please make sure to commit all your changes " \
            "before going further. All uncommited changes will be lost."
        _print_step(options, 1)

    elif options.step == 1:
        check_call(['git', 'reset', '--hard'])
        check_call(['git', 'clean', '-f', '-d'])
        branch = check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
        check_call(['git', 'pull', '--rebase', 'origin', branch])
        if len(check_output(['git', 'status', '-z']).strip()) != 0:
            print _color_bar
            print _colorize("The pull isn't fast forward.", RED)
            print _colorize("Please solve the rebase and run it again.", YELLOW)
            exit(1)

        check_call(['git', 'submodule', 'foreach', 'git', 'fetch'])
        check_call(['git', 'submodule', 'foreach', 'git', 'checkout', options.version])
        check_call([
            'git', 'submodule', 'foreach', 'git', 'reset',
            '--hard', options.version
        ])
        check_call(['git', 'submodule', 'foreach', 'git', 'submodule', 'sync'])
        check_call(['git', 'submodule', 'foreach', 'git', 'submodule', 'update', '--init'])
        check_call([
            'wget',
            'http://raw.github.com/camptocamp/c2cgeoportal/%s/'
            'c2cgeoportal/scaffolds/create/versions.cfg'
            % options.version, '-O', 'versions.cfg'
        ])
        check_call(['make', '-f', options.file, 'build'])

        check_call([
            '.build/venv/bin/pcreate', '--interactive', '-s', 'c2cgeoportal_update',
            '../%s' % project['project_folder'], 'package=%s' % project['project_package']
        ])

        diff_file = open("changelog.diff", "w")
        check_call(['git', 'diff', 'CONST_CHANGELOG.txt'], stdout=diff_file)
        diff_file.close()

        print
        print _color_bar
        print "Do manual migration steps based on what’s in the CONST_CHANGELOG.txt file" \
            " (listed in the `changelog.diff` file)."
        _print_step(options, 2)

    elif options.step == 2:
        if options.file is None:
            print "The makefile is missing"
            exit(1)

        if path.isfile('changelog.diff'):
            unlink("changelog.diff")

        check_call(['make', '-f', options.file, 'build'])

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

        print
        print _color_bar
        print "The upgrade is nearly done, now you should:"
        print "- Test your application."

        _print_step(options, 3, intro="Then to commit your changes type:")

    elif options.step == 3:
        if not _test_checkers(project):
            _print_step(options, 3, intro="Correct them then type:")
            exit(1)

        shutil.rmtree('old')
        check_call(['git', 'add', '-A'])
        check_call(['git', 'commit', '-m', 'Update to GeoMapFish %s' % options.version])


def deploy(options):
    project = _get_project()
    if not _test_checkers(project):
        print _colorize("Correct them and run again", RED)
        exit(1)

    check_call(['sudo', '-u', 'deploy', 'deploy', '-r', 'deploy/deploy.cfg', options.host])
    check_call(['make', '-f', options.file, 'build'])


if __name__ == "__main__":  # pragma: no cover
    main()
