Paste Deployment
================

.. py:module:: fanstatic

Fanstatic has support for `Paste Deployment`_, a system for
configuring WSGI applications and servers. You can configure the
Fanstatic WSGI components using Paste Deploy.

Fanstatic WSGI component
------------------------

If you have configured your application with Paste, you will already
have a configuration ``.ini`` file, say ``deploy.ini``. You can now
wrap your application in the :py:func:`Fanstatic` WSGI component::

  [server:main]
  use = egg:Paste#http

  [app:my_application]
  use = egg:myapplication

  [pipeline:main]
  pipeline = fanstatic my_application

  [filter:fanstatic]
  use = egg:fanstatic#fanstatic

The :py:func:`Fanstatic` WSGI framework component actually itself
combines three separate WSGI components - the :py:class:`Injector`,
the :py:class:`Delegator` and the :py:class:`Publisher` - into one
convenient component.

The ``[filter:fanstatic]`` section accepts several configuration
directives (see also the :doc:`configuration documentation
<configuration>`):

Turn recomputing of hashes on or off with "true" or "false"::

  recompute_hashes = true

To turn versioning on or off with "true" or "false"::

  versioning = true

You can also configure the URL segment that is used in generating URLs
to resources and to recognize "serve-able" resource URLs::

  publisher_signature = foo

To allow for bottom inclusion of resources::

  bottom = true

To force *all* Javascript to be included at the bottom::

  force_bottom = true

To serve ``minified`` resources where available::

  minified = True

To serve ``debug`` resources where available::

  debug = True

Use rolled up resources where possible and where they are available::

  rollup = true

Use bundling of resources::

  bundle = true

A complete ``[filter:fanstatic]`` section could look like this::

  [filter:fanstatic]
  use = egg:fanstatic#fanstatic
  recompute_hashes = false
  versioning = true
  bottom = true
  minified = true

The Fanstatic WSGI component is all you should need for normal use
cases. Next, we will go into the details of what the sub-components
that this component consists of. These should only be useful in
particular use cases when you want to take over some of the task of
Fanstatic itself.

Injector WSGI component
-----------------------

If you don't want to use the Publisher component as you want to serve
the libraries yourself, you can still take care of injecting URLs by
configuring the :py:class:`Injector` WSGI component separately::

  [server:main]
  use = egg:Paste#http

  [app:my_application]
  use = egg:myapplication

  [pipeline:main]
  pipeline = injector my_application

  [filter:injector]
  use = egg:fanstatic#injector

The ``[filter:injector]`` section accepts the same set of
configuration parameters as the ``[filter:fanstatic]`` section. A
complete section therefore could look like this::

  [filter:injector]
  use = egg:fanstatic#injector
  recompute_hashes = false
  versioning = false
  bottom = true
  minified = true

Publisher WSGI component
------------------------

It is also possible to set up the ``Publisher`` component separately.
The publisher framework component is actually a combination of a
:py:class:`Delegator` and a :py:class:`Publisher` component. The
delegator is responsible for recognizing what URLs are in fact URLs to
"serve-able" resources, passing along all other URLs to be handled by
your application.

The delegator recognizes URLs that contain the ``publisher_signature``
as a path segment are recognized as "serve-able". Configuring only the
publisher component for your application implies that there is some
other mechanism that injects the correct resources URLs into, for
example, web pages.

The publisher component accepts one configuration directive, the
``publisher_signature`` (default it's set to ``fanstatic``)::

  [server:main]
  use = egg:Paste#http

  [app:my_application]
  use = egg:myapplication

  [pipeline:main]
  pipeline = publisher my_application

  [filter:publisher]
  use = egg:fanstatic#publisher
  publisher_signature = bar

Combining the publisher and the injector
----------------------------------------

As explained before, the :py:func:`Fanstatic` component combines the
publisher and injector components. An equivalent configuration using
the separate components would look like this::

  [server:main]
  use = egg:Paste#http

  [app:my_application]
  use = egg:myapplication

  [pipeline:main]
  pipeline = publisher injector my_application

  [filter:publisher]
  use = egg:fanstatic#publisher
  publisher_signature = baz

  [filter:injector]
  use = egg:fanstatic#injector
  recompute_hashes = false
  versioning = true
  bottom = true
  minified = true
  publisher_signature = baz

.. _`Paste Deployment`: http://pythonpaste.org/deploy/

