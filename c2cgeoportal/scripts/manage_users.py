# -*- coding: utf-8 -*-
import os.path
import logging.config
import warnings
from optparse import OptionParser
from ConfigParser import ConfigParser

from pyramid.paster import get_app
import transaction


def main():
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
Reset a user password.\nThe username is used as password if the password is not \
provided with the corresponding option.\nuser can be created if it doesnt exist.'

    parser = OptionParser(usage)
    parser.add_option('-i', '--iniconfig', default='production.ini',
      help='project .ini config file')
    parser.add_option('-p', '--password', help='set password (if not set, username is \
used as password)')
    parser.add_option('-c', '--create', action="store_true", default=False,
      help='create user if it doesnt already exist')
    parser.add_option('-r', '--rolename', default='role_admin',
      help='the role name which must exist in the database')

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("you must specify a username")

    username = args[0]
    ini_file = options.iniconfig

    if not os.path.isfile(ini_file):
        raise StandardError('the config file %s can not be found' % ini_file)

    logging.config.fileConfig(ini_file)
    log = logging.getLogger(__name__)

    # loading schema name from config and setting its value to the
    # corresponding global variable from c2cgeoportal

    # Ignores pyramid deprecation warnings
    warnings.simplefilter('ignore', DeprecationWarning)

    config = ConfigParser()
    config.read(ini_file)
    section = 'app:c2cgeoportal'
    option = 'project'
    if not config.has_section(section):
        raise StandardError('the config file %s has no %s section' % (ini_file, section))
    if not config.has_option(section, option):
        raise StandardError('the config file %s has no %s option in %s section ' % \
                            (ini_file, option, section))
    app = get_app(ini_file, config.get(section, option))
    settings = app.registry.settings
    schema = settings['schema']

    # must be done only once we have loaded the project config
    from c2cgeoportal import models

    print "\n"

    # check that User and Role exist in model
    modelList = ['User', 'Role']
    for model in modelList:
        try:
            usertable = getattr(models, model)
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
            query_role = sess.query(models.Role).filter(models.Role.name == u'%s' % \
                         options.rolename)

            if query_role.count() == 0:
                # role not found in db?
                raise StandardError('role matching %s doesnt exists in database' % \
                                    options.rolename)

            role = query_role.first()

            user = models.User(username=u'%s' % username,
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


def get_password(password, username):
    if password is not None:
        # if password is provided, use passwrd
        return password
    else:
        return username

if __name__ == "__main__":
    main()
