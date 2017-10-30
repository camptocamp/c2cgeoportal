Authentication
--------------

The default policy
~~~~~~~~~~~~~~~~~~

By default ``c2cgeoportal`` applications use an *auth ticket* authentication
policy (``AuthTktAuthenticationPolicy``). With this policy the user name is
obtained from the "auth ticket" cookie set in the request.

The policy is created, and added to the application's configuration, in the
application's main ``__init__.py`` file.

Using another policy
~~~~~~~~~~~~~~~~~~~~

When using ``AuthTktAuthenticationPolicy`` an "auth ticket" cookie should be
set in the request for the user to be identified. In some applications using
another identification mechanism may be needed.

Example with a "remote user" policy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For example, in a project of ours, the c2cgeoportal application needs to
integrate with the Nevis single sign-on environment. This SSO system is
composed of a central auth server, and a proxy running as an Apache module.
The proxy takes care of communicating with the auth server, and sets the
username in the ``REMOTE_USER`` environment variable when the user has been
identified. With this system an "auth ticket" policy cannot be used, obviously.
A `"remote user" authentication policy
<http://docs.pylonsproject.org/projects/pyramid/en/1.3-branch/api/authentication.html#pyramid.authentication.RemoteUserAuthenticationPolicy>`_
should be used instead.

To use a "remote user" authentication policy edit the application's
main ``__init__.py`` file, and set ``authentication_policy`` to a
``RemoteUserAuthenticationPolicy`` instance:

.. code:: python

   from pyramid.config import Configurator
   from pyramid.authentication import RemoteUserAuthenticationPolicy
   from c2cgeoportal_geoportal import locale_negotiator
   from c2cgeoportal_geoportal.resources import FAModels, defaultgroupsfinder
   from ${package}.resources import Root

   def main(global_config, **settings):
       """ This function returns a Pyramid WSGI application.
       """
       authentication_policy = RemoteUserAuthenticationPolicy(
               callback=defaultgroupsfinder)
       config = Configurator(root_factory=Root, settings=settings,
               locale_negotiator=locale_negotiator,
               authentication_policy=authentication_policy)
       # ...

``c2cgeoportal`` provides an authentication policy callback, namely
``defaultgroupsfinder``, that is appropriate in most cases. This callback
assumes that ``request.user.role`` is a reference to the ``Role`` database
object (more information below). This callback is required for admin users to
be able to access to the admin interface.

It is important to note that when using a "remote user" authentication policy
the authentication process is delegated to an outside system. So calls to
``pyramid.security.remember`` and ``pyramid.security.forget``, as done in
c2cgeoportal's ``login`` and ``logout`` views, have no effect.

With an authentication policy set in the application configuration the user
name can be obtained by calling ``request.unauthenticated_userid``.
(This function returns ``None`` if there is currently no authenticated user.)
But c2cgeoportal applications need to also know about the user's *role* to
work properly.

So when using an external authentication system this system should also provide
the c2cgeoportal application with the name of the user's role. This can be done
in ``apache/wsgi.conf.mako`` by relying on the `mod_setenvif
<http://httpd.apache.org/docs/2.2/mod/mod_setenvif.html>`_ Apache module's
``SetEnvIf`` directive. For example::

    SetEnvIf isiwebsectoken <role>(.*)</role> rolename=$1

or::

    SetEnvIf isiwebsectoken '<field name="roles">([a-zA-Z0-9,\.]*)</field>' rolename=$1

With this ``mod_setenvif`` extracts the role name from the ``isiwebsectoken`` header
and places it in the ``rolename`` environment variable. See the ``mod_setenvif``
documentation for more details.

The connection between the nevisProxy and the application is established using
an Apache module called NINAP. The above Apache configuration may also contain
NINAP directives (see nevisProxy documentation). For instance to indicate what
field in the ``isiwebsectoken`` header contains the username::

    NINAP_UserPattern '<field name="loginId">([a-zA-Z0-9\._-]*)</field>'

Eventually the following directives activate the access restriction to the
application::

    <Location /<instance_id>/wsgi>
      AuthType sectoken
      Require valid-user
    </Location>

The ``c2cgeoportal`` code expects that the user data (user name, role name and
user functionalities) are available through the ``user`` property in the
``request`` object. More specifically it expects ``request.user.role.id`` to
contain the role id, and ``request.user.role.name`` to contain the role name.
``request.user.username`` and ``request.user.functionalities`` must be provided
as well.
Therefore the application should redefine the callback function that adds
a ``user`` property to the request. This is done by calling the
``set_request_property`` function on the ``Configurator`` object.
You may for example add to ``__init__.py``:

.. code:: python

    def get_user_from_request(request, username):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role
        class O:
            pass
        if username is None:
            username = request.unauthenticated_userid
        if username is not None:
            user = O()
            user.username = username
            rolename = request.environ.get('rolename')
            user.role_name = rolename
            user.role = DBSession.query(Role).filter_by(name=rolename).one()
            user.functionalities = []
            return user

And then, in the application's ``main`` function:

.. code:: python

    config.set_request_property(
            get_user_from_request, name='user', property=True)
    config.set_request_property(
            get_user_from_request, name='get_user')

Please note that ``c2cgeoportal`` expects the admin role to be ``role_admin``.
If for some reason you need to use another name for this role, you may define
an alias in a project-specific callback and use it instead of the standard
``defaultgroupsfinder`` as ``AuthenticationPolicy`` argument in ``__init__.py``::

    def mygroupsfinder(username, request):
        role = request.user.role
        if role:
            if role.name == '<your_admin_rolename>':
                return ['role_admin']
            return [role.name]
        return []

    def main(global_config, **settings):
        ...
        authentication_policy = RemoteUserAuthenticationPolicy(
            callback=mygroupsfinder)
        ...

.. note::

    ``c2cgeoportal`` registers its own request property callback for ``user``.
    The one registered by the application overwrites it.

You should be set at this point.

Custom user validation
~~~~~~~~~~~~~~~~~~~~~~

For logging in ``c2cgeoportal`` validates the user credentials
(username/password) by reading the user information from the ``user`` database
table. If a c2cgeoportal application should work with another user information
source, like LDAP, another *client validation* mechanism should be set up.
``c2cgeoportal`` provides a specific ``Configurator`` function for that, namely
``set_user_validator`` which allow to register a custom validator.
Here is an example:

.. code:: python

    def custom_user_validator(request, username, password):
        from pyramid_ldap import get_ldap_connector
        connector = get_ldap_connector(request)
        data = connector.authenticate(username, password)
        if data is not None:
            return data[0]
        return None
    ...
    config.set_user_validator(custom_user_validator)

The validator function is passed three arguments: ``request``, ``username``,
and ``password``. The function should return a string containing all the data
you want to keep if the credentials are valid, and ``None`` otherwise.

In this example the `pyramid_ldap package
<http://docs.pylonsproject.org/projects/pyramid_ldap/en/latest/>`_ is used as
the user information source.

User validators can obviously be chained. For example, a user validator
function that queries the ``user`` database table if the user does not exist in
LDAP would look like this:

.. code:: python

    def custom_user_validator(request, username, password):
        from c2cgeoportal_geoportal import default_user_validator
        from pyramid_ldap import get_ldap_connector
        connector = get_ldap_connector(request)
        data = connector.authenticate(username, password)
        if data is not None:
            return data[0]
        return default_user_validator(request, username, password)

Custom user validation - LDAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Full example using pyramid_ldap, see `# LDAP` / `# END LDAP` blocs.

.. code:: python

    # -*- coding: utf-8 -*-

    from pyramid.config import Configurator
    # LDAP
    # get_user_from_request also needed for the same reason
    from c2cgeoportal_geoportal import locale_negotiator, add_interface, \
        INTERFACE_TYPE_NGEO, get_user_from_request
    # END LDAP
    from c2cgeoportal_geoportal.lib.authentication import create_authentication
    from yourproject.resources import Root

    import logging

    # LDAP
    # dependencies
    import ldap
    from json import dumps, loads
    # END LDAP

    log = logging.getLogger(__name__)

    # LDAP
    # authenticate on LDAP and return cleaned user data
    def custom_user_validator(request, username, password):
        from c2cgeoportal_geoportal import default_user_validator
        from pyramid_ldap import get_ldap_connector
        connector = get_ldap_connector(request)
        data = connector.authenticate(username, password)

        if data is not None:
            log.debug('user %s found in ldap' % username)
            log.debug(pp.pformat(data[1]))
            user = {'username': data[1]['uid'][0], 'role': data[1]['roles'][0]}
            return dumps(user)

        log.debug("user %s not found in ldap, searching locally" % username)
        return default_user_validator(request, username, password)

    # get custom user data from request and link with existing c2cgeoportal
    # role in your project
    def custom_get_user_from_request(request, identity):

        class O:
            pass

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role

        if hasattr(request, '_user') and identity is None:
            # avoid recursive calls from
            # get_user_from_request -> request.authenticated_userid -> ...
            return request._user

        user = get_user_from_request(request)
        if user is None:
            log.debug("user is not authenticated or is a ldap user")
            if identity is None:
               identity = request.unauthenticated_userid
            if identity is not None:
                identity = loads(identity)
                user = O()
                user.username = identity['username']
                user.functionalities = []
                user.is_password_changed = True
                user.role_name = identity['role']
                user.role = DBSession.query(Role).filter_by(name=identity['role']).one()
                user.id = -1
                request._user = user

        return user
    # END LDAP

    def main(global_config, **settings):
        """ This function returns a Pyramid WSGI application.
        """
        config = Configurator(
            root_factory=Root, settings=settings,
            locale_negotiator=locale_negotiator,
            authentication_policy=create_authentication(settings)
        )

        config.include("c2cgeoportal")

        # LDAP
        # dependencies
        config.include('pyramid_ldap')

        # LDAP config
        config.ldap_setup(
            'ldap://ldap.server.host',
            bind='CN=ldap user,CN=Users,DC=example,DC=com',
            passwd='ld@pu5er'
        )

        config.ldap_set_login_query(
            base_dn='CN=Users,DC=example,DC=com',
            filter_tmpl='(uid=%(login)s)',
            scope = ldap.SCOPE_ONELEVEL,
            )

        config.ldap_set_groups_query(
            base_dn='CN=Users,DC=example,DC=com',
            filter_tmpl='(&(objectCategory=group)(member=%(userdn)s))',
            scope = ldap.SCOPE_SUBTREE,
            cache_period = 600,
            )
        # END LDAP

        # scan view decorator for adding routes
        config.scan()

        # add the interfaces
        add_interface(config)
        add_interface(config, "edit")
        add_interface(config, "routing")
        add_interface(config, "mobile", INTERFACE_TYPE_NGEO)

        # LDAP
        # register the customized function
        config.set_user_validator(custom_user_validator)
        config.add_request_method(custom_get_user_from_request, 'user', property=True)
        config.add_request_method(custom_get_user_from_request, 'get_user')
        # END LDAP

        return config.make_wsgi_app()
