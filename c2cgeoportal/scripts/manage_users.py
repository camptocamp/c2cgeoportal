# -*- coding: utf-8 -*-

# Copyright (c) 2011-2017, Camptocamp SA
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
import argparse
import warnings

from pyramid.paster import get_app, setup_logging
import transaction


def main():
    """
    Emergency user create and password reset script
    example, reset toto password to foobar:
    .build/venv/bin/manage_users -p foobar toto
    example, create user foo with password bar and role admin:
    .build/venv/bin/manage_users -c -r role_admin -p bar foo

    to get the options list, do:
    .build/venv/bin/manage_users -h
    """

    usage = """Usage: %prog [options] USERNAME

Reset a user password.
The username is used as password if the password is not provided with the corresponding option.
User can be created if it does not exist yet."""

    parser = argparse.ArgumentParser(description=usage)
    parser.add_argument(
        "-i", "--app-config",
        default="production.ini", dest="app_config",
        help="The application .ini config file (optional, default is "
        "'production.ini')"
    )
    parser.add_argument(
        "-n", "--app-name",
        default="app", dest="app_name",
        help="The application name (optional, default is 'app')"
    )
    parser.add_argument(
        "-p", "--password",
        help="Set password (if not set, username is used as password"
    )
    parser.add_argument(
        "-c", "--create",
        action="store_true", default=False,
        help="Create user if it does not already exist"
    )
    parser.add_argument(
        "-r", "--rolename",
        default="role_admin",
        help="The role name which must exist in the database"
    )
    parser.add_argument(
        "-e", "--email",
        default=None,
        help="The user email"
    )
    parser.add_argument(
        'user',
        nargs='1',
        help="The user"
    )

    options = parser.parse_args()
    username = options.user

    app_config = options.app_config
    app_name = options.app_name

    if app_name is None and "#" in app_config:
        app_config, app_name = app_config.split("#", 1)
    if not os.path.isfile(app_config):
        parser.error("Cannot find config file: {0!s}".format(app_config))

    # loading schema name from config and setting its value to the
    # corresponding global variable from c2cgeoportal

    # Ignores pyramid deprecation warnings
    warnings.simplefilter("ignore", DeprecationWarning)

    setup_logging(app_config)
    get_app(app_config, name=app_name)

    # must be done only once we have loaded the project config
    from c2cgeoportal import models

    print("\n")

    # check that User and Role exist in model
    model_list = ["User", "Role"]
    for model in model_list:
        try:
            getattr(models, model)
        except AttributeError:
            print("models.{0!s} not found".format(model))

    # check that user exists
    sess = models.DBSession()
    query = sess.query(models.User).filter_by(username=u"{0!s}".format(username))

    result = query.count()
    if result == 0:
        if not options.create:
            # if doesn"t exist and no -c option, throw error
            raise Exception("User {0!s} does not exist in database".format(username))
        else:
            print("User {0!s} does not exist in database, creating".format(username))
            # if does not exist and -c option, create user

            password = options.password if options.password is not None else username
            email = options.email if options.email is not None else username

            # get roles
            query_role = sess.query(models.Role).filter(
                models.Role.name == u"{0!s}".format(options.rolename))

            if query_role.count() == 0:
                # role not found in db?
                raise Exception("Role matching {0!s} does not exist in database".format(
                    options.rolename
                ))

            role = query_role.first()

            user = models.User(
                username=u"{0!s}".format(username),
                password=u"{0!s}".format(password),
                email=u"{0!s}".format(email),
                role=role
            )
            sess.add(user)
            transaction.commit()

            print("User {0!s} created with password {1!s} and role {2!s}".format(
                username, password, options.rolename
            ))

    else:
        # if user exists (assuming username are unique)
        user = query.first()

        if options.password is not None:
            print("Password set to: {0!s}".format(options.password))
            user.password = u"{0!s}".format(options.password)

        if options.email is not None:
            user.email = options.email

        sess.add(user)
        transaction.commit()

        print("Password resetted for user {0!s}".format(username))


if __name__ == "__main__":
    main()
