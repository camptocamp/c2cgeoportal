.. _integrator_ngeo:

ngeo
====

Organization
------------

Simple and advanced modes
~~~~~~~~~~~~~~~~~~~~~~~~~

The HTML and the JS of an interface are in the files:
``geoportal/<package>_geoportal/static-ngeo/js/apps/<interface>.html.ejs`` and
``geoportal/<package>_geoportal/static-ngeo/js/apps/Controller<interface>.js``
where ``<interface>`` is the interface name.

In all application modes (simple and full):

The style sheet file is ``geoportal/<package>_geoportal/static/css/<interface>.css``.

The header file is ``geoportal/<package>_geoportal/static/header.html``.

The images used from the admin interface should be placed in the folder ``geoportal/<package>_geoportal/static/images/``.

Advanced mode only
~~~~~~~~~~~~~~~~~~

The style sheet vars file is ``geoportal/<package>_geoportal/static-ngeo/js/apps/sass/vars_<interface>.scss``.

The style sheet file is ``geoportal/<package>_geoportal/static-ngeo/js/apps/sass/<interface>.scss``.

The images used by the application code should be placed in the folder ``geoportal/<package>_geoportal/static-ngeo/images/``.


HTML file
---------

.. note::

    This is not possible in the simple application mode

In this file, you can add some blocks like

.. code:: html

   <gmf-auth-panel slot="tool-panel-auth"></gmf-auth-panel>

to include a web-component in a specific slot (one UI part of the app).

You can find the available component in the :ngeo_doc:`ngeo documentation </apidoc/>`.

The controller (``js`` file) is commonly named ``mainCtrl``. So you can use a value
from the controller by doing the following (here, the controller is the ``DesktopController``):

.. code:: html

    <html lang="{{desktopCtrl.lang}}" ng-app="mydemo" ng-controller="DesktopController as mainCtrl">
      <head>
      ...
      </head>
      <body>
      ...
      <gmf-mycomponent
        slot="map"
        gmf-mycomponent-variableproperty="mainCtrl.open"
        gmf-component-staticproperty="::mainCtrl.map">
      <gmf-component>
      ...
      </body>
    </html>


Controller (js file)
--------------------

.. note::

    This is not possible in the simple application mode

In the controller you have some lines like:

.. code:: javascript

   import gmf<Component>Module from 'gmf/<component>/module';

This is needed to include the javascript of the used component.

You can add your own imports.

Most of the component configuration and the map configuration is in the ``interfaces_config`` section
of the vars file. See the section below.

Dynamic.json view
-----------------

To configure the ngeo constants with dynamic or configurable values,
you can use the dynamic view.

This view is configurable in the vars files in the section ``interfaces_config``.
The sub section is the interface name, and after that we have:

* ``redirect_interface``: Interface to be redirected to if an unexpected device type is used (mobile/desktop).
* ``do_redirect``: Directly do the redirect.
* ``extends``: Interface for which the ``constants``, ``dynamic_constants``, ``static`` and ``routes`` shall
  be extended. These values will be updated with the interface configuration
  (but can not be removed via interface configuration).
* ``constants``: Directly define a constant in the vars file.
* ``dynamic_constants``: Define a constant from a dynamic values.
* ``static``, the ``key`` is the constant name:
    * ``name``: The path of the resource whose URL we want to have e.g.
        ``/etc/geomapfish/static/contextualdata.html``.
    * ``append``: A text we want to append.
* ``routes``, the ``key`` is the constant name:
    * ``name``: Name of the route whose URL we want to have.
    * ``kw``: Keyword arguments to supply for dynamic path elements in the route definition.
    * ``elements``: Additional positional path segments to append to the URL after it is generated.
    * ``params``: Query string parameters to append to the URL (available parameters of our services: :ref:`developer_webservices`).
    * ``dynamic_params``: Query string parameters from dynamic values to append to the URL.

    For more information regarding the ``elements`` and ``kw`` properties see the *Pyramid*
    ``Request.route_url`` `documentation
    <https://docs.pylonsproject.org/projects/pyramid/en/latest/api/request.html#pyramid.request.Request.route_url>`_.

* ``lang_urls_suffix`` suffix used in l10n URL, see: :ref:`integrator_multi_organization`.

The dynamic values names are:

* ``interface``: The interface name given in the parameters of the dynamic view.
* ``cache_version``: The version of the cache.
* ``two_factor``: Two factor authentication status from `vars.authentication.two_factor`.
* ``lang_urls``: The language URL for AngularJS dynamic locale.
* ``i18next_configuration``: The i18next configuration from `vars.i18next.backend` with dynamically calculated `loadPath`,
* ``fulltextsearch_groups``: The search groups from the `layer_name` of the Full-Text Search table.

Ngeo configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: //ngeo_configuration.rst

Ngeo API configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: //ngeo_api_configuration.rst

Ngeo internal object configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. include:: //ngeo_config_ref.rst
.. include:: //ngeo_other_configuration.rst


CSS style
---------

Simple and advanced modes
~~~~~~~~~~~~~~~~~~~~~~~~~

In the ``gmfOptions`` we have a ``cssVars`` property where we can configure all CSS variable
(``var(--a-variable)`` in the css files.

The content of ``cssVars`` is a dictionary where the keys are the CSS variable names, and the values the
value to be set to the CSS variable.
For the CSS variables named ``brand-primary`` and ``brand-secondary`` we also calculated the other colors
related to those variable as it's done in the SCSS, to be able to change the major application colors.

The components of the interface are using Shadow DOM (in open mode). That means that their style is protected
and not accessible through the main css file. To change the styling of a component, you can inject
your style with the ``gmfCustomCSS`` constants in the vars.yaml file. Example:

.. code:: yaml

    <interface>:
      constants:
        gmfCustomCSS:
          authentication: '<selector> {<property>: <value>;}'

Advanced mode only
~~~~~~~~~~~~~~~~~~

In the advanced mode, you can set the style of a component by selecting the component using
the ``querySelector`` native function and by appending a new style to this element.
Example:

.. code:: js

    const style = document.createElement( 'style' )
    style.innerHTML = '<selector> {<property>: <value>;}'
    document.querySelector('<my-component-selector>').shadowRoot.appendChild(style);

Or alternatively, you can override a component to access and modify the ``render`` function. In this
function, you can modify the `customCSS_` property to set directly your own style. This way is not
recommended if you don't have to override the component for another purpose.

Creating your own component
---------------------------

.. note::

    This is not possible in the simple application mode

Create your ``.ts`` file in a dedicated folder under:
``geoportal/<package>_geoportal/static-ngeo/js/``. We encourage you to use LitElement web-components.

For the structure, you can be inspired by one of the (not AngularJS) components in ngeo. For instance, the
``src/auth/FormElement.ts``.

Here's a ``Hello <name>`` component:

.. code:: typescript

  // File ...static-ngeo/js/custom/helloWorld.ts;
  import {html, TemplateResult, CSSResult, css} from 'lit';
  import {customElement, property} from 'lit/decorators.js';
  import GmfBaseElement from 'gmfapi/elements/BaseElement';
  import i18next from 'i18next';

  @customElement('hello-world')
  export default class GmfAuthForm extends GmfBaseElement {
    @property({type: String}) name = 'Unknow';

    connectedCallback(): void {
      super.connectedCallback();
    }

    static styles: CSSResult[] = [
      ...GmfBaseElement.styles,
      css`
        .name {
          color: green;
        }
      `,
    ];

    protected render(): TemplateResult {
      return html`
        <div>
          <span>${i18next.t('Hello')}&nbsp;</span>
          <span class="name">${this.name}</span>
        </div>
      `;
    }
  }

Then load your component in the controller of one of your interfaces:

.. code:: javascript

   import GmfAuthForm from '../custom/helloWorld';

At this point, if in your <interface> HTML app file you declare your component, it should be loaded:

.. code:: html

   <hello-world name="Demo"></hello-world>

It should print ``Hello Demo`` (with "Demo" in a green color).

If you have no error and no result, verify that the component is correctly declared and loaded.
A custom markup in the HTML is not an error and no error will be thrown if the component is
not loaded at all.

Every information that could be used by multiple components should be stored in a ``store``. Our stores are based on the
``rxjs`` library. Existing stores in ngeo are in `srcapi/store`.

Logic between a store and a component should be stored in a singleton ("service").
A singleton is a class with only one instantiation. This instance is exported and usable everywhere in
the code. Example in ngeo: `src/auth/service.ts`.

We recommend to minimize the amount of code within your component, and to use reusable external classes,
static functions, helper and utils files instead. It will facilitate the maintenance.

Extending or overriding an existing component
---------------------------------------------

.. note::

    This is not possible in the simple application mode

Overriding an existing component is possible but you have to test carefully your code
after each GMF update as the original code may have changed.

You can define some new functions or new variables to a class via the prototype. Here's an example with
the ngeo auth form component:

.. code:: typescript

   import GmfAuthForm from 'ngeo/auth/FormElement';

   GmfAuthForm.prototype.myNewValue;

   GmfAuthForm.prototype.newFunction = function () {};

To replace an existing function, just create a function with the same name than the one to replace:

.. code:: typescript

   GmfAuthForm.prototype.logout(evt: Event): void {
     console.log('I do nothing but print a message');
   };

You will have to copy-paste the content of the original function to keep the component working. But you
can modify it.

Finally be sure that the file where you override or extend existing content is read by the main
controller file of your app:

.. code:: javascript

   import '../custom/myOverridenComponent.js';

.. note::

    You can do the same with every "store", "service", function, etc. as long as the original piece
    of code you want to override is exported.

.. note::

    The ``constructor`` of a class is not modifiable. If you want to modify to logic inside a
    constructor, you must copy the original class to a new custom class and use it instead of the original one.
    In some cases, you may use inheritance (with the ``extends`` keyword) to limit the copy-paste.
