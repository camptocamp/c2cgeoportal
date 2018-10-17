# -*- coding: utf-8 -*-

# Copyright (c) 2011-2018, Camptocamp SA
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
import transaction
import warnings

from c2cgeoportal_geoportal.scripts import fill_arguments, get_app


def main():
    """
    Emergency user create and password reset script
    example, reset toto password to foobar:
    ./docker-compose-run manage_users --password=foobar toto
    example, create user foo with password bar and role admin:
    ./docker-compose-run manage_users --create --rolename=role_admin --password=bar foo

    to get the options list, do:
    ./docker-compose-run manage_users --help
    """

    usage = """Usage: %prog [options] USERNAME

Reset a user password.
The username is used as password if the password is not provided with the corresponding option.
User can be created if it does not exist yet."""

    parser = argparse.ArgumentParser(description=usage)
    fill_arguments(parser)
    parser.add_argument(
        "--password", "-p",
        help="Set password (if not set, username is used as password"
    )
    parser.add_argument(
        "--create", "-c",
        action="store_true", default=False,
        help="Create user if it does not already exist"
    )
    parser.add_argument(
        "--rolename", "-r",
        default="role_admin",
        help="The role name which must exist in the database"
    )
    parser.add_argument(
        "--email", "-e",
        default=None,
        help="The user email"
    )
    parser.add_argument(
        'user',
        nargs=1,
        help="The user"
    )

    options = parser.parse_args()
    username = options.user

    # loading schema name from config and setting its value to the
    # corresponding global variable from c2cgeoportal_geoportal

    # Ignores pyramid deprecation warnings
    warnings.simplefilter("ignore", DeprecationWarning)

    get_app(options, parser)

    # must be done only once we have loaded the project config
    from c2cgeoportal_commons.models import DBSession, main, static

    print("\n")

    # check that user exists
    sess = DBSession()
    query = sess.query(static.User).filter_by(username="{0!s}".format(username))

    result = query.count()
    if result == 0:
        if not options.create:
            # if doesn"t exist and no -c option, throw error
            raise Exception("User {0!s} does not exist in database".format(username))
        else:
            print(("User {0!s} does not exist in database, creating".format(username)))
            # if does not exist and -c option, create user

            password = options.password if options.password is not None else username
            email = options.email if options.email is not None else username

            # get roles
            query_role = sess.query(main.Role).filter(
                main.Role.name == "{0!s}".format(options.rolename))

            if query_role.count() == 0:
                # role not found in db?
                raise Exception("Role matching {0!s} does not exist in database".format(
                    options.rolename
                ))

            role = query_role.first()

            user = static.User(
                username="{0!s}".format(username),
                password="{0!s}".format(password),
                email="{0!s}".format(email),
                role=role
            )
            sess.add(user)
            transaction.commit()

            print(("User {0!s} created with password {1!s} and role {2!s}".format(
                username, password, options.rolename
            )))

    else:
        # if user exists (assuming username are unique)
        user = query.first()

        if options.password is not None:
            print(("Password set to: {0!s}".format(options.password)))
            user.password = "{0!s}".format(options.password)

        if options.email is not None:
            user.email = options.email

        sess.add(user)
        transaction.commit()

        print(("Password reset for user {0!s}".format(username)))


if __name__ == "__main__":
    main()
