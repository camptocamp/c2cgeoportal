.. _integrator_authentication:

Authentication
==============

The default policy
------------------

By default ``c2cgeoportal`` applications use an *auth ticket* authentication
policy (``AuthTktAuthenticationPolicy``). With this policy the user name is
obtained from the "auth ticket" cookie set in the request.

The policy is created, and added to the application's configuration, in the
application's main ``__init__.py`` file.

Using another policy
--------------------

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
``RemoteUserAuthenticationPolicy`` instance::

    from pyramid.config import Configurator
    from pyramid.authentication import RemoteUserAuthenticationPolicy
    from c2cgeoportal import locale_negotiator
    from c2cgeoportal.resources import FAModels, defaultgroupsfinder
    from ${package}.resources import Root

    def auth_policy_callback(username, request):
        # this function is called when either unauthenticated_userid
        # or effective_principals is called

        from c2cgeoportal.models import AUTHORIZED_ROLE

        rolename = request.environ.get('rolename')
        assert rolename is not None

        return [AUTHORIZED_ROLE] if rolename == 'role_admin' else []


    def main(global_config, **settings):
        """ This function returns a Pyramid WSGI application.
        """
        authentication_policy = RemoteUserAuthenticationPolicy(
                callback=auth_policy_callback)
        config = Configurator(root_factory=Root, settings=settings,
                locale_negotiator=locale_negotiator,
                authentication_policy=authentication_policy)
        # ...

The callback (``auth_policy_callback`` here) is required for the admin
interface. If it was not set admin users would not be able to access the admin
interface.  The callback defined here assumes that the role name is set in the
``rolename`` environment variable. We come back to this below.

It is important to note that when using a "remote user" authentication policy
the authentication process is delegated to an outside system. So calls to
``pyramid.security.remember`` and ``pyramid.security.forget``, as done in
c2cgeoportal's ``login`` and ``logout`` views, have no effect.

With an authentication policy set in the application configuration the user
name can be obtained by calling ``pyramid.security.unauthenticated_userid``.
(This function returns ``None`` if there's currently no authenticated user.)
But c2cgeoportal applications need to also know about the user's *role* to
work properly.

So when using an external authentication system this system should also provide
the c2cgeoportal application with the name of the user's role. This can be done
by relying on the `mod_setenvif
<http://httpd.apache.org/docs/2.2/mod/mod_setenvif.html>`_ Apache module's
``SetEnvIf`` directive. For example::

    SetEnvIf sectoken <role>(.*)</role> rolename=$1

With this ``mod_setenvif`` extracts the role name from the ``sectoken`` header
and places it in the ``rolename`` environment variable. See the ``mod_setenvif``
documentation for more detail. You should now be able to better understand
what the ``auth_policy_callback`` function does.

The ``c2cgeoportal`` code expects that the user data (user name and role name)
is available through the ``user`` property in the ``request`` object. More
specifically it expects ``request.user.role.id`` to contain the role id (id of
the role record in the database). To provide ``c2cgeoportal`` with what it
expects the application should redefine the callback function that adds
a ``user`` property to the request. This is done by calling the
``set_request_property`` function on the ``Configurator`` object.  For
example::

    from pyramid.security import unauthenticated_userid

    def get_user_from_request(request):
        from c2cgeoportal.models import DBSession, Role
        class O(object):
            pass
        username = unauthenticated_userid(request)
        if username is not None:
            user = O()
            rolename = self.environ.get('rolename')
            user.role = DBSession.query(Role).filter_by(
                            name=rolename).one()
            return user

And then, in the application's ``main`` function::

    config.add_request_property(get_user_from_request,
                                name='user', reify=True
                                )

The ``reify`` argument is to ``True`` to cache the function's return value and
actually execute the function only once per request. In this example the user
name is obtained by calling ``unauthenticated_userid``, itself relying on the
authentication policy set in the application. The role object is obtained from
the value of the ``rolename`` environment variable by querying the database.

.. note::

    ``c2cgeoportal`` registers its own request property callback for ``user``.
    The registered by the application overwrites it.

You should be set at this point.
