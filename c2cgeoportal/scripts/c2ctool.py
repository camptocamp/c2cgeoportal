# -*- coding: utf-8 -*-

# Copyright (c) 2013, Camptocamp SA
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


import sys
from subprocess import call, check_output
from argparse import ArgumentParser


def main():  # pragma: no cover
    """
    tool used to help th use in the user tash
    """

    usage = """usage: {prog} [command] [options]

Available commands:

\x1b[01;32mhelp\x1b[0m: show this page
\x1b[01;32mbuild\x1b[0m: build the application
\x1b[01;32mupdate\x1b[0m: update the application code
\x1b[01;32mupgrade\x1b[0m: upgrade the application to a new version
\x1b[01;32mbuildoutcmds\x1b[0m: show the buildout commands

To have some help on a command type:
{prog} help [command]""".format(prog=sys.argv[0])

    if len(sys.argv) <= 1:
        print usage
        exit()

    if sys.argv[1] == 'help':
        if len(sys.argv) > 2:
            parser = fill_arguments(sys.argv[2])
            parser.print_help()
        else:
            print usage
        exit()

    parser = fill_arguments(sys.argv[1])
    options = parser.parse_args(sys.argv[2:])

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


def fill_arguments(command):
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
        pass
    elif command == 'upgrade':
        parser.add_argument(
            'version', metavar='VERSION', help='uUpdate to version'
        )
    elif command == 'buildoutcmds':
        pass
    else:
        print "Unknown command"
        exit()

    return parser


def build(options):
    import zc.buildout.buildout

    sys.argv = ['./buildout/bin/buildout', '-c', options.file]

    if options.cmd:
        sys.argv += ['install']
        sys.argv += [options.cmd]
    elif options.desktop:
        sys.argv += ['install', 'template', 'jsbuild', 'cssbuild']
    elif options.mobile:
        sys.argv += ['install', 'jsbuild-mobile', 'mobile']

    zc.buildout.buildout.main()

    call(['sudo', 'apache2ctl', 'graceful'])


def update(options):
    branch = check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip()
    print "Use branch %s." % branch
    call(['git', 'pull', 'origin', branch])
    call(['git', 'submodule', 'sync'])
    call(['git', 'submodule', 'update', '--init'])
    call(['git', 'submodule', 'foreach', 'git', 'submodule', 'sync'])
    call(['git', 'submodule', 'foreach', 'git', 'submodule', 'update', '--init'])


def upgrade(options):
    print "TODO"


def readBuildoutFile(name, help):
    from ConfigParser import ConfigParser
    config = ConfigParser()
    config.read(name)

    if config.has_option('buildout', 'extends'):
        readBuildoutFile(config.get('buildout', 'extends'), help)

    for cmd in config.sections():
        if config.has_option(cmd, 'help'):
            help[cmd] = config.get(cmd, 'help')


def buildoutcmds(options):
    help = {}
    readBuildoutFile('buildout.cfg', help)

    for cmd, help in help.items():
        # for cmd not in ['buildout', 'versions', 'eggs', 'activate']
        print "\x1b[01;32m%s\x1b[0m: %s" % (cmd, help)


if __name__ == "__main__":  # pragma: no cover
    main()
