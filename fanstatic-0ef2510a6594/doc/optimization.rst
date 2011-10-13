Optimization
============

.. py:module:: fanstatic

There are various optimizations for resource inclusion that Fanstatic
supports. Because some optimizations can make debugging more
difficult, the optimizations are disabled by default.

We will summarize the optimization features that Fanstatic offers
here. See the :doc:`configuration section<configuration>` and the
:doc:`API documentation <api>` for more details.

* minified resources. Resources can specify minified versions using
  the mode system. You can then configure Fanstatic to preferentially
  serve resources in a certain mode, such as ``minified``.

* rolling up of resources.  Resource libraries can specify rollup
  resources that combine multiple resources into one. This reduces the
  amount of server requests to be made by the web browser, and can
  help with caching. This can be controlled with the ``rollup`` configuration
  parameter.

* bundling of resources.  Resource bundles combine multiple resources into one.
  This reduces the amount of server requests to be made by the web browser, and
  help with caching. This can be controlled with the ``bundle`` configuration
  parameter.

* infinite caching. Fanstatic can serve resources declaring that they
  should be cached forever by the web browser (or proxy cache),
  reducing the amount of hits on the server. Fanstatic makes this safe
  even when you upgrade or modify resources by its versioning
  technology. This can be controlled with the ``versioning`` and
  ``recompute_hashes`` configuration parameters.

* Javascript inclusions at the bottom of the web page. This can speed
  up the time web pages render, as the browser can start displaying
  the web page before all Javascript resources are loaded. This can be
  controlled using the ``bottom`` and ``force_bottom`` configuration
  parameters.

To find out more about these and other optimizations, please read this
`best practices article`_ that describes some common optimizations to
speed up page load times.

.. _`best practices article`: http://developer.yahoo.com/performance/rules.html
