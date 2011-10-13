Configuration options
=====================

.. py:module:: fanstatic

Fanstatic makes available a number of configuration options. These can
be passed to the :py:class:`Fanstatic` WSGI component as keyword
arguments.  They can also be configured using `Paste Deploy`_
configuration patterns (see :doc:`our Paste Deploy documentation
<paste_deploy>` for more information on that).

.. _`Paste Deploy`: http://pythonpaste.org/deploy/

versioning
----------

If you turn on versioning, Fanstatic will automatically include a
version identifier in the resource URLs it generates and injects into
web pages. This means that for each version of your Javascript
resource its URL will be unique. The Fanstatic publisher will set
cache headers for versioned resource URLs so that they will be cached
forever by web browsers and caching proxies [#well]_.

By default, versioning is disabled, because it needs some extra
explanation.  We highly recommend you to enable it however, as the
performance benefits are potentially huge and it's usually entirely
safe to do so. See also ``recompute_hashes`` if you want to use versioning
during development.

The benefit of versioning is that all resources will be cached forever
by web browsers. This means that a web browser will never talk to the
server to request a resource again once it retrieved it once, as long
as it is still in its cache. This puts less load on your web
application: it only needs to publish the resource once for a user, as
long as the resource remains in that user's cache.

If you use a server-side cache such as Squid or Varnish, the situation
is even better: these will hold on to the cached resources as well,
meaning that your web application needs to serve the resource exactly
*once*. The cache will serve them after that.

But what if you change a resource? Won't users now get the wrong, old
versions of the changed resource?  No: with versioning enabled, when you
change a resource, a *new* URL to that resource will be automatically
generated. You never will have to instruct users of your web
application to do a "shift-reload" to force all resources to reload --
the browser will see the resource URL has changed and will
automatically load a new one.

How does this work? There are two schemes: explicit versioning and an
automatically calculated hash-based versioning. An explicit version
looks like this (from the :pypi:`js.jquery` package)::

  /fanstatic/jquery/:version:1.4.4/jquery.js

A hash-based version looks like this::

  /fanstatic/my_library/:version:d41d8cd98f00b204e9800998ecf8427e/my_resource.js

The version of Resource depends on the version of the python package
in which the Library is defined: it takes the explicit version
information from this. If no version information can be found or if
the python package is installed in `development mode`_, we still want
to be able to create a unique version that changes whenever the
content of the resources changes.

To this end, the most recent modification time from the files and directories
in the Library directory is taken. Whenever you make any changes to a resource
in the library, the hash version will be automatically recalculated.

The benefit of calculating a hash for the Library directory is that
resource URLs change when a referenced resource changes; If resource A
(i.e. ``logo.png``) in a library that is referenced by resource B
(i.e. ``style.css``) changes, the URL for resource A changes, not
because A changed, but because the contents of the library to which A
and B belong has changed.

Fanstatic also provides an MD5-based algorithm for the Library version
calculation. This algorithm is slower, but you may use if you don't trust
your filesystem. Use it through the ``versioning_use_md5`` parameter.


.. _`development mode`: http://peak.telecommunity.com/DevCenter/setuptools#develop

recompute_hashes
----------------

If you enable ``versioning``, Fanstatic will automatically calculate
a resource hash for each of the resource directories for which no version
is found.

During development you want the hashes to be recalculated each time you
make a change, without having to restart the application all the time,
and having a little performance impact is no problem. The default behavior
is to recompute hashes for every request.

Calculating a resource hash is a relatively expensive operation, and
in production you want Fanstatic to calculate the resource hash only
once per library, by setting ``recompute_hashes`` to false. Hashes will
then only be recalculated after you restart the application.

bottom
------

While CSS resources can only be included in the ``<head>`` section of
a web page, Javascript resources can be included in ``<script>`` tags
anywhere on the web page. Sometimes it pays off to do so: by including
Javascript resources at the bottom of a web page (just before the
``</body>`` closing tag), the page can already load and partially
render for the user before the Javascript files have been loaded, and
this may lead to a better user experience.

Not all Javascript files can be loaded at this time however: some
depend on being included as early as possible. You can mark a
:py:class:`Resource` as "bottom safe" if they are safe to
load at the bottom of the web page. If you then enable ``bottom``,
those Javascript resources will be loaded there. If ``bottom`` is
turned off (the default), all Javascript resources will be included
in the ``<head>`` section.

force_bottom
------------

If you enable ``force_bottom`` (default it's disabled) then if you
enable ``bottom``, *all* Javascript resources will be included at the
bottom of a web page, even if they're not marked "bottom safe".

minified and debug
------------------

By default, the resource URLs included will be in the normal
human-readable (and debuggable) format for that resource.

When creating :py:class:`Resource` instances, you can specify
alternative modes for the resource, such as minified and debug
versions. The argument to ``minified`` and ``debug`` are a resource
path or resource that represents the resource in that alternative mode.

You can configure Fanstatic so that it prefers a certain mode when
creating resource URLs, such as ``minified``. In this case Fanstatic
will preferentially serve minified alternatives for resources, if
available. If no minified version is available, the default resource
will be served.

rollup
------

A performance optimization to reduce the amount of requests sent by a
client is to roll up several resources into a bundle, so that all
those resources are retrieved in a single request. This way a whole
collection of resources can be served in one go.

You can create special :py:class:`Resource` instances that declare
they supersede a collection of other resources. If ``rollup`` is
enabled, Fanstatic will serve a combined resource if it finds out that
all individual resources that it supersedes are needed. If you also
declare that a resource is an ``eager_superseder``, the rolled up
resource will actually always be served, even if only some of the
superseded resources are needed.

base_url
--------

The ``base_url`` URL will be prefixed in front of all resource
URLs. This can be useful if your web framework wants the resources to
be published on a sub-URL. By default, there is no ``base_url``, and
resources are served in the script root.

Note that this can also be set using the ``set_base_url`` method on a
:py:class:`NeededResources` instance during run-time, as this URL is
generally not known when :py:class:`NeededResources` is instantiated.

publisher_signature
-------------------

The default publisher signature is ``fanstatic``. What this means is
that the :py:func:`Fanstatic` WSGI component will look for the string
``/fanstatic/`` in the URL path, and if it's there, will take over to
publish resources. If you would like the root for resource publication
to be something else in your application (such as ``resources``), you
can change this to another string.

bundle
------

Bundling of resources minimizes HTTP requests from the client by finding
efficient bundles of resources. In order to configure bundling of resources,
set the ``bundle`` argument to True. 

.. [#well] Well, for 10 years into the future at least.

