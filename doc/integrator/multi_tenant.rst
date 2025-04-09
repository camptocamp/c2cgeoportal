.. _integrator_multi_tenant:

Multi-tenant
============

The geoportal can host multiple organizations, with configuration differences for each organization.
In a multi-organization geoportal, each organization will have the same program code
(Python, Javascript, SCSS). In this mode all the organizations are served by the same infrastructure.

In this example we will have the came CSS but we can do some variations by using CSS var,
see ``cssVars`` in ``gmfOptions`` in the ngeo GMF constants definitions
:ngeo_doc:`gmf constants </jsdoc/module-contribs_gmf_src_options.html>`.

The following lines will provide a basic implementation for multi-tenant.

The code should be adapted, currently it handles the hostnames 'org1.camptocamp.com' and
'org2.camptocamp.com', and you probably want to put the hardcoded values in the config.

``multi_tenant.py``
-------------------

You should have a ``geoportal/<package>_geoportal/multi_tenant.py`` file like this one:

.. code:: python

    from pyramid.config import Configurator


    def get_instance_prefix(request):
        if request.host == "org1.camptocamp.com":
            return "org1"
        if request.host == "org2.camptocamp.com":
            return "org2"
        # Can be used to debug the application
        return os.environ.get("DEFAULT_PREFIX", "unknown")


    def get_organization_role(request, role_type):
        prefix = get_instance_prefix(request)
        return f"{prefix}-{role_type}"


    def get_organization_interface(request, interface):
        prefix = get_instance_prefix(request)
        return f"{prefix}-{interface}"


    def get_organization_print_url(request):
        prefix = get_instance_prefix(request)
        print_url = request.registry.settings["print_url"]
        # Custom code can be added to have a different behavior
        return print_url


    def includeme(config: Configurator) -> None:
       """Initialize the multi-tenant."""

        config.add_request_method(
            get_organization_role, name="get_organization_role")
        config.add_request_method(
            get_organization_interface, name="get_organization_interface")
        config.add_request_method(
            get_organization_print_url, name="get_organization_print_url")

``vars.yaml``
-------------

In the file ``geoportal/vars.yaml`` add the following in interfaces the ``interfaces_config``:

.. code:: yaml

    org1-desktop:
        extends: desktop
        redirect_interface: mobile
        lang_urls_suffix: -org1
        constants:
            ...
    org1-mobile:
        extends: mobile
        redirect_interface: desktop
        lang_urls_suffix: -org1
        constants:
            ...
    org2-desktop:
        extends: desktop
        redirect_interface: mobile
        lang_urls_suffix: -org2
        constants:
            ...
    org2-mobile:
        extends: mobile
        redirect_interface: desktop
        lang_urls_suffix: -org2
        constants:
            ...

Roles
-----

The following roles should be created and completed as needed
(the original roles ``anonymous``, ``registered`` and ``intranet`` are no more used)::

- org1-anonymous
- org1-registered
- org1-intranet
- org2-anonymous
- org2-registered
- org2-intranet

Internationalization
--------------------

For each organization, a set of localization file should be created.

First you should create a ``tenants.yaml`` file like that:

.. code:: yaml

    tenants:
      org1:
        public_url: https://org1.camptocamp.com
        suffix: -org1
        curl_args: <optional>
      org2:
        ...

The general workflow is:

- run ``scripts/multi-tenant-update-po``.
- This will run one ``make update-po-from-url`` for each organization with different environment variables.
- The result is one po file set for each organization with the defined suffix.
- The integrator needs to complete the po files with translations.
- When the config Docker image is built, all po files are automatically converted to JSON files
  with the same suffix.
- At runtime, the ``dynamic`` view will return the appropriate URLs for the translations.

Configuration
.............

Add this rule in the ``geoportal/Makefile``:

.. code::

   .PHONY: update-client-po
   update-client-po:
       # Generate po file for org1
       cd .. && SUFFIX=-org1 INTERFACES=desktop-org1,mobile-org1 \
           update-po $(USER_ID) $(GROUP_ID) $(LANGUAGES)
       # Generate po file for org2
       cd .. && SUFFIX=-org2 INTERFACES=desktop-org2,mobile-org2 \
           update-po $(USER_ID) $(GROUP_ID) $(LANGUAGES)

       # Example with all environment variables
       cd .. && \
           SUFFIX=-test \
           INTERFACES=desktop-test,mobile-test \
           THEME_REGEX=.*-test \
           GROUP_REGEX=.*-test \
           WMSLAYER_REGEX=.*-test \
           WMTSLAYER_REGEX=.*-test \
           update-po $(USER_ID) $(GROUP_ID) $(LANGUAGES)

The environment variables that are used by the ``update-po`` command are the following:

 - ``INTERFACES``: List of interfaces we want to use.
 - ``THEME_REGEX``: Regular expression used to filter the themes.
 - ``GROUP_REGEX``: Regular expression used to filter the layer groups.
 - ``WMSLAYER_REGEX``: Regular expression used to filter the WMS layers.
 - ``WMTSLAYER_REGEX``: Regular expression used to filter the WMTS layers.

Note that the extractor is able to filter themes and layers based on the given interfaces but there is no
link between layer groups and interfaces.


Modify the ``Dockerfile`` to create all the needed localization JSON files:

.. code::

   - RUN build-l10n "<package>"
   + RUN build-l10n --suffix=-org1 --suffix=-org2 "<package>"


When loading the frontend, the ``dynamic`` view will return the appropriate localization URLs based on the
``lang_urls_suffix`` defined in the corresponding interface (in ``interfaces_config``).
See the definition above.


Stylesheet, Title and other UI customization
--------------------------------------------

Note: This is also working in simple mode.

To be able to have some Stylesheet per tenant create a CSS file named
``geoportal/geomapfish_geoportal/static/css/<tenant>.css`` and use it in the tenant interfaces with e.-g.:

.. code:: yaml

  vars:
    interfaces_config:
      <tenant>-desktop:
        static:
          gmfCustomStylesheetUrl:
            name: /etc/geomapfish/static/css/grancy.css

To be able to have some title per tenant create a file named
``geoportal/geomapfish_geoportal/static/tenant.js``, with:

.. code:: javascript

  let tenant = gmfapi.store.config.getConfig().getValue().tenantOptions;
  if (tenant.title !== undefined) {
    // Don't be updated by AngularJS
    let title = document.querySelector('title');
    if (title) {
      title.remove();
    }
    document.title = tenant.title;
  }

Then use it in the default interfaces:

.. code:: yaml

  vars:
    interfaces_config:
      default:
        static:
          gmfCustomJavascriptUrl:
            name: /etc/geomapfish/static/tenant.js

And configure it in the tenant interfaces:

.. code:: yaml

  vars:
    interfaces_config:
      <tenant>-desktop:
        constants:
          tenantOptions:
            title: Tenant title - Desktop


Warning
-------

With that, one user of the org1 can login to the organization org2 and will have the ``registered`` rights.
