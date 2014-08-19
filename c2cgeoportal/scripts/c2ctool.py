# -*- coding: utf-8 -*-

# Copyright (c) 2014, Camptocamp SA
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
from subprocess import call
from argparse import ArgumentParser
from ConfigParser import ConfigParser

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
""" + _colorize("build", GREEN) + """: build the application
""" + _colorize("update", GREEN) + """: update the application code
""" + _colorize("upgrade", GREEN) + """: upgrade the application to a new version
""" + _colorize("deploy", GREEN) + """: deploy the application to a server
""" + _colorize("buildoutcmds", GREEN) + """: show the buildout commands

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

    if sys.argv[1] == 'build':
        build(options)
    elif sys.argv[1] == 'update':
        update(options)
    elif sys.argv[1] == 'upgrade':
        upgrade(options)
    elif sys.argv[1] == 'buildoutcmds':
        buildoutcmds(options)
    else:
        print "Unknown command"


def _fill_arguments(command):
    parser = ArgumentParser(prog="%s %s" % (sys.argv[0], command), add_help=False)
    if command == 'help':
        parser.add_argument(
            'command', metavar='COMMAND', help='The command'
        )
    elif command == 'build':
        parser.add_argument(
            'file', metavar='BUILDOUT_FILE', help='The buildout file used to build'
        )
        parser.add_argument(
            '--desktop', action='store_true',
            help='Build only task needed for the desktop application.'
        )
        parser.add_argument(
            '--mobile', action='store_true',
            help='Build only task needed for the mobile application.'
        )
        parser.add_argument(
            '--cmd', '-c', action='append',
            help='Build a specific buildout task.'
        )
    elif command == 'update':
        parser.add_argument(
            'file', metavar='BUILDOUT_FILE', help='The buildout file used to build'
        )
    elif command == 'upgrade':
        parser.add_argument(
            'file', metavar='BUILDOUT_FILE', help='The buildout file used to build', default=None
        )
        parser.add_argument(
            '--step', type=int, help=argparse.SUPPRESS, default=0
        )
        parser.add_argument(
            'version', metavar='VERSION', help='Upgrade to version'
        )
    elif command == 'buildoutcmds':
        pass
    else:
        print "Unknown command"
        exit()

    return parser


def _run_buildout_cmd(file='buildout.cfg', commands=[]):
    import zc.buildout.buildout

    sys.argv = ['./buildout/bin/buildout', '-c', file]

    if len(commands) > 0:
        sys.argv += ['install']
        sys.argv += commands

    zc.buildout.buildout.main()


def build(options):
    cmds = []
    if options.cmd:
        cmds = options.cmd
    elif options.desktop:
        cmds = ['install', 'template', 'jsbuild', 'cssbuild']
    elif options.mobile:
        cmds = ['install', 'jsbuild-mobile', 'mobile']

    _run_buildout_cmd(options.file, cmds)

    call(['sudo', '/usr/sbin/apache2ctl', 'graceful'])


def update(options):
    branch = check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
    print "Use branch %s." % branch
    call(['git', 'pull', 'origin', branch])
    call(['git', 'submodule', 'sync'])
    call(['git', 'submodule', 'update', '--init'])
    call(['git', 'submodule', 'foreach', 'git', 'submodule', 'sync'])
    call(['git', 'submodule', 'foreach', 'git', 'submodule', 'update', '--init'])

    _run_buildout_cmd('CONST_buildout_cleaner.cfg')
    shutil.rmtree('old')

    _run_buildout_cmd(options.file)
    call(['sudo', '/usr/sbin/apache2ctl', 'graceful'])


def _print_step(options, step, intro="To continue type:"):
    global _command_to_use
    print intro
    print _colorize("%s upgrade %s %s --step %i", YELLOW) % (
        _command_to_use,
        options.file if options.file is not None else "<buildout_user.cfg>",
        options.version, step
    )


def upgrade(options):
    from yaml import load
    import c2cgeoportal.scripts.manage_db

    if not path.isfile('project.yaml'):
        print "Unable to find the required 'project.yaml' file."
        exit(1)

    project = load(file('project.yaml', 'r'))

    if options.step == 0:
        if path.split(path.realpath('.'))[1] != project['project_folder']:
            print "Your project isn't in the right folder!"
            print "It should be in folder '%s' instead of folder '%s'." % (
                project['project_folder'], path.split(path.realpath('.'))[1]
            )

        call(['git', 'status'])
        print
        print _color_bar
        print "Here is the output of 'git status'. Please make sure to commit all your changes " \
            "before going further. All uncommited changes will be lost."
        _print_step(options, 1)

    elif options.step == 1:
        call(['git', 'status'])
        call(['git', 'reset', '--hard'])
        call(['git', 'clean', '-f', '-d'])
        branch = check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
        call(['git', 'pull', 'origin', branch])
        call(['git', 'submodule', 'foreach', 'git', 'fetch'])
        call([
            'git', 'submodule', 'foreach', 'git', 'reset',
            '--hard', 'origin/%s' % options.version
        ])
        call(['git', 'submodule', 'foreach', 'git', 'submodule', 'sync'])
        call(['git', 'submodule', 'foreach', 'git', 'submodule', 'update', '--init'])
        call([
            'wget',
            'http://raw.github.com/camptocamp/c2cgeoportal/%s/'
            'c2cgeoportal/scaffolds/create/versions.cfg'
            % options.version, '-O', 'versions.cfg'
        ])
        _run_buildout_cmd(commands=['eggs'])

        call([
            './buildout/bin/pcreate', '--interactive', '-s', 'c2cgeoportal_update',
            '../%s' % project['project_folder'], 'package=%s' % project['project_package']
        ])

        diff_file = open("changelog.diff", "w")
        call(['git', 'diff', 'CONST_CHANGELOG.txt'], stdout=diff_file)
        diff_file.close()

        print
        print _color_bar
        print "Do manual migration steps based on what’s in the CONST_CHANGELOG.txt file" \
            " (listed in the `changelog.diff` file)."
        _print_step(options, 2)

    elif options.step == 2:
        if project.file is None:
            print "The buildout file is missing"
            exit(1)

        buildout_config = ConfigParser()
        buildout_config.read(project.file)
        if buildout_config.has_option('buildout', 'develop'):
            print(
                "The user buildout file shouldn't override the `develop`"
                " option of the `[buildout]` section."
            )
            exit(1)
        if buildout_config.has_option('version', 'c2cgeoportal'):
            print "The user buildout file shouldn't specify the `c2cgeoportal` version"
            exit(1)

        unlink("changelog.diff")

        _run_buildout_cmd('CONST_buildout_cleaner.cfg')
        shutil.rmtree('old')

        _run_buildout_cmd(options.file)

        sys.argv = ['./buildout/bin/manage_db', 'upgrade']
        c2cgeoportal.scripts.manage_db.main()

        print
        print _color_bar
        print "The upgrade is nearly done, now you should:"
        print "- build your application with:"
        print "- Test your application."

        _print_step(options, 3, intro="Then to commit your changes type:")

    elif options.step == 3:
        http = httplib2.Http()
        for check_type in ["", "type=all"]:
            resp, content = http.request(
                "http://localhost/%s%s" % (project['checker_path'], check_type),
                method='GET',
                headers={
                    "Host": project['host']
                }
            )
            if resp.status < 200 or resp.status >= 300:
                print(_color_bar)
                print "Checker error:"
                print "Open `http://%s/%s%s` for more informations." % (
                    project['host'], project['checker_path'], check_type
                )
                print_step(options, 3, intro="Correct them then type:")
                exit(1)

        call(['git', 'add', '-A'])
        call(['git', 'commit', '-m', '"Update to GeoMapFish %s"' % options.version])


def _read_buildout_files_help(name, commands_help):
    from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read(name)

    if config.has_option('buildout', 'extends'):
        _read_buildout_files_help(config.get('buildout', 'extends'), commands_help)

    for cmd in config.sections():
        if config.has_option(cmd, 'help'):
            commands_help[cmd] = config.get(cmd, 'help')


def buildoutcmds(options):
    commands_help = {}
    _read_buildout_files_help('buildout.cfg', commands_help)

    for cmd, command_help in commands_help.items():
        # for cmd not in ['buildout', 'versions', 'eggs', 'activate']
        print "%s: %s" % (_colorize(cmd, GREEN), command_help)


if __name__ == "__main__":  # pragma: no cover
    main()
