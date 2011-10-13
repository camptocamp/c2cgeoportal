Serf: A standalone Fanstatic WSGI application
=============================================

.. py:module:: fanstatic

During development of Javascript code it can be useful to test your
Javascript code in a very simple HTML page. Fanstatic contains a very
simple WSGI application that allows you to do this: Serf.

The :py:class:`Serf` class is a WSGI application that serves a very
simple HTML page with a ``<head>`` and ``<body>`` section. You can
give the Serf class a single resource to include. If you wrap the Serf
WSGI application in a :py:class:`Fanstatic` WSGI framework
component, the resource and all its dependencies will be included on
the web page.

Paste Deployment of Serf
------------------------

Serf is mostly useful in combination with `Paste Deployment`_, as this
makes it very easy to configure a little test web application. You
configure Fanstatic as discussed in the :doc:`our Paste Deploy
documentation <paste_deploy>` section. You then add a serf app in a
``app:`` section and tell it what resource to include using the
``py:<dotted_name>`` notation.

A dotted name is a string that refers to a Python object. It consists
of a packages, modules and objects joined together by dots, much as
you can write them in Python ``import``
statements. ``js.jquery.jquery`` for instance refers to the ``jquery``
resource in the ``js.jquery`` package. This way you can refer to any
package on your Python path (controlled by buildout or virtualenv).

Finally, you also must include the Serf application in the WSGI
pipeline.

Here is a full example which includes the jquery resource on a HTML
page::

  [server:main]
  use = egg:Paste#http

  [app:serf]
  use = egg:fanstatic#serf
  resource = py:js.jquery.jquery

  [filter:fanstatic]
  use = egg:fanstatic#fanstatic

  [pipeline:main]
  pipeline = fanstatic serf

.. _`Paste Deployment`: http://pythonpaste.org/deploy/
