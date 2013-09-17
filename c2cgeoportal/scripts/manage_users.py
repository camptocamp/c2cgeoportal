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


import os.path
import warnings
from optparse import OptionParser

from pyramid.paster import get_app
import transaction


def main():  # pragma: no cover
    """
    emergency user create and password reset script
    exemple, reset toto password to foobar:
    ./buildout/bin/manage_users -p foobar toto
    exemple, create user foo with password bar and role admin:
    ./buildout/bin/manage_users -c -r role_admin -p bar foo

    to get the options list, do:
    ./buildout/bin/manage_users -h
    """

    usage = 'usage: %prog [options] USERNAME \n\n\
Reset a user password.\nThe username is used as password if the password is not provided with the corresponding option.\nuser can be created if it doesnt exist.'  # NOQA

    parser = OptionParser(usage)
    _help = 'The application .ini config file (optional, '\
            'default is production.ini)'
    parser.add_option('-i', '--app-config', default='production.ini',
                      dest='app_config', help=_help)
    _help = 'The application name (optional, default is "app")'
    parser.add_option('-n', '--app-name', default="app",
                      dest='app_name', help=_help)
    _help = 'set password (if not set, username is ' \
            'used as password'
    parser.add_option('-p', '--password', help=_help)
    parser.add_option(
        '-c', '--create', action="store_true", default=False,
        help='create user if it doesnt already exist')
    parser.add_option(
        '-r', '--rolename', default='role_admin',
        help='the role name which must exist in the database')

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("you must specify a username")

    username = args[0]

    app_config = options.app_config
    app_name = options.app_name

    if app_name is None and '#' in app_config:
        app_config, app_name = app_config.split('#', 1)
    if not os.path.isfile(app_config):
        parser.error('Can\'t find config file: %s' % app_config)

    # loading schema name from config and setting its value to the
    # corresponding global variable from c2cgeoportal

    # Ignores pyramid deprecation warnings
    warnings.simplefilter('ignore', DeprecationWarning)

    get_app(app_config, name=app_name)

    # must be done only once we have loaded the project config
    from c2cgeoportal import models

    print "\n"

    # check that User and Role exist in model
    modelList = ['User', 'Role']
    for model in modelList:
        try:
            getattr(models, model)
        except AttributeError:
            print "models.%s not found" % model

    # check that user exists
    sess = models.DBSession()
    query = sess.query(models.User).filter_by(username=u'%s' % username)

    result = query.count()
    if result == 0:
        if not options.create:
            # if doesnt existe and no -c option, throw error
            raise StandardError('user %s doesnt exists in database' % username)
        else:
            print 'user %s doesnt exists in database, creating' % username
            # if doesnt existe and -c option, create user

            password = get_password(options.password, username)

            # get roles
            query_role = sess.query(models.Role).filter(
                models.Role.name == u'%s' % options.rolename)

            if query_role.count() == 0:
                # role not found in db?
                raise StandardError(
                    'role matching %s doesnt exists in database' %
                    options.rolename)

            role = query_role.first()

            user = models.User(
                username=u'%s' % username,
                password=u'%s' % password,
                email=u'%s' % username,
                role=role
            )
            sess.add(user)
            transaction.commit()

            print "user %s created with password %s and role %s" % \
                (username, password, options.rolename)

    else:
        # if user exists (assuming username are unique)
        user = query.first()

        password = get_password(options.password, username)

        print "password set: %s" % password

        user.password = u'%s' % password
        sess.add(user)
        transaction.commit()

        print "password reseted for user %s" % username


def get_password(password, username):  # pragma: no cover
    if password is not None:
        # if password is provided, use passwrd
        return password
    else:
        return username

if __name__ == "__main__":  # pragma: no cover
    main()
