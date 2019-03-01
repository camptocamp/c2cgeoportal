# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019, Camptocamp SA
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

from c2cgeoportal_commons.testing import get_session
from c2cgeoportal_geoportal.scripts import fill_arguments, get_appsettings


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
        help="The user"
    )
    options = parser.parse_args()
    username = options.user
    settings = get_appsettings(options)

    with transaction.manager:
        sess = get_session(settings, transaction.manager)

        # Must be done only once we have loaded the project config
        from c2cgeoportal_commons.models import main, static

        print("\n")

        # Check that user exists
        query = sess.query(static.User).filter_by(username=username)

        result = query.count()
        if result == 0:
            if not options.create:
                # If doesn't exist and no -c option, throw error
                print("User {} does not exist in database".format(username))
                exit(1)
            else:
                if options.password is None:
                    parser.error("The password is mandatory on user creation")
                if options.email is None:
                    parser.error("The email is mandatory on user creation")

                # Get roles
                query_role = sess.query(main.Role).filter(main.Role.name == options.rolename)

                if query_role.count() == 0:
                    # Role not found in db?
                    print("Role matching {} does not exist in database".format(options.rolename))
                    exit(1)

                role = query_role.first()

                user = static.User(
                    username=username,
                    password=options.password,
                    email=options.email,
                    settings_role=role,
                    roles=[role]
                )
                sess.add(user)

                print(("User {} created with password {} and role {}".format(
                    username, options.password, options.rolename
                )))

        else:
            # If user exists (assuming username are unique)
            user = query.first()

            if options.password is not None:
                print("Password set to: {}".format(options.password))
                user.password = "{}".format(options.password)

            if options.email is not None:
                user.email = options.email

            sess.add(user)

            print("Password reset for user {}".format(username))


if __name__ == "__main__":
    main()
