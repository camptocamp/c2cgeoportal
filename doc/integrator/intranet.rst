.. _integrator_intranet:

Intranet Users Detection
========================

It may be interesting to assign a default role to anonymous users connecting
from a given IP or set of IP addresses (eg. intranet users).

The default username and role for anonymous intranet users as well as the
matching IP regexp are configured in ``<package>.mk`` (see step #4 below).
The assigned role must obviously have been defined in the administration interface.

Example of accepted IP setting:

.. code:: yaml

    intranet_ip = 12.34.56.78
    intranet_ip = ^12.34.(.*)

This page lists the changes that must be applied to add such a functionality.

1. Edit ``<package>/__init__.py``. Add the following line:

   .. code:: python

       from c2cgeoportal_geoportal import _create_get_user_from_request

   Add the following function:

   .. code:: python

       def custom_get_user_from_request(request):
           if 'anonymous' in request.params:
               return None

           get_user_from_request = _create_get_user_from_request(request.registry.settings)
           user = get_user_from_request(request)

           if user is None and request.environ.get('intranet', 0) == '1':
               from c2cgeoportal_commons.models import DBSession, Role
               class O(object):
                   pass
               user = O()
               user.username = request.registry.settings.get('intranet_default_user', 'Intranet')
               user.functionalities = []
               user.is_password_changed = True
               try:
                   rolename = request.registry.settings.get('intranet_default_role', 'intranet')
                   user.role_name = rolename
                   user.role = DBSession.query(Role).filter_by(name=rolename).one()
                   user.role_id = -1
                   user.id = -1
               except:
                   request.environ['authFailed'] = True
                   user = None
           return user

   In the ``main()`` function before

   .. code:: python

       return config.make_wsgi_app()

   add

   .. code:: python

       config.set_request_property(custom_get_user_from_request,
                                   name='user', reify=True
       )

2. In the ``vars`` section of ``vars.yaml`` add

   .. code:: yaml

       # intranet detection
       intranet_ip = <IP address or regexp>
       intranet_default_user = 'Intranet'
       intranet_default_role = 'role_intranet'

3. At the end of ``<package>.mk`` add

   .. code:: make

        CONFIG_VARS += intranet_default_user intranet_default_role

4. In ``<package>/templates/index.html`` replace

   .. code:: python

       <script type="text/javascript" src="${request.route_url('viewer')}${extra_params}

   by

   .. code:: python

       <%
       anonymous_param = '&anonymous' if 'anonymous' in request.params else ''
       %>
       <script type="text/javascript" src="${request.route_url('viewer')}${extra_params}${anonymous_param}"></script>

5. In ``<package>/templates/viewer.js`` and ``<package>/templates/edit.js`` add at the beginning:

   .. code:: python

       <%
       mapserverProxyUrl = request.route_url('mapserverproxy')
       if 'anonymous' in request.params:
           mapserverProxyUrl += '?anonymous'
       %>

   and replace all occurences of

   .. code:: python

       ${request.route_url('mapserverproxy')}

   or

   .. code:: python

       ${request.route_url('mapserverproxy')}

   by

   .. code:: python

       ${mapserverProxyUrl}
