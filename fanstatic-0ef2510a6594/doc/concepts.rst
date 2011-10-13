Concepts
========

To understand Fanstatic, it's useful to understand the following
concepts.

Library
-------

Static resources are files that are used in the display of a web page,
such as CSS files, Javascript files and images. Often resources are
packaged as a collection of resources; we call this a *library* of
resources.

Resource inclusion
------------------

Resources can be included in a web page in several ways.

A common forms of inclusion in HTML are Javascript files, which are
included using the ``script`` tag, for instance like this::

  <script type="text/javascript" src="/something.js"></script>

and CSS files, which are included using a ``link`` tag, like this::

  <link rel="stylesheet" href="/something.css" type="text/css" />

A common way for Javascript and CSS to be included is in ``head``
section of a HTML page. Javascript can also be included in script tags
elsewhere on the page, such as at the bottom.

Fanstatic can generate these resource inclusions automatically for you
and insert them into your web page.

Fanstatic doesn't do anything special for the inclusion of image or
file resources, which could be included by the ``img`` or ``a``
tag. While Fanstatic can serve these resources for you, and also knows
how to generate URLs to them, Fanstatic does not automatically insert
them into your web pages: that's up to your application.

Resource definitions
--------------------

Fanstatic lets you define resources and their dependencies to make the
automated rendering of resource inclusions possible.

You can see a resource inclusion as a Python import: when you import a
module, you import a particular file in a particular package, and a
resource inclusion is the inclusion of a particular resource (``.js``
file, ``.css`` file) in a particular library.

A resource may depend on other resources. A Javascript resource may
for instance require another Javascript resource. An example of this
is jQuery UI, which requires the inclusion of jQuery on the page as
well in order to work.

Fanstatic takes care of inserting these resources inclusions on your
web page for you. It makes sure that resources with dependencies have
their dependencies inserted as well.

Resource requirements
---------------------

How do you tell Fanstatic that you'd like to include jQuery on a web
page? You do this by making an *resource requirement* in Python: you
state you *need* a resource.

It is common to construct complex web pages on the server with
cooperating components. A datetime widget may for instance expect a
particular datetime Javascript library to be loaded. Pages but also
sub-page components on the server may have inclusion requirements; you
can effectively make resource requirements anywhere on the server
side, as long as the code is executed somewhere during the request
that produces the page.
