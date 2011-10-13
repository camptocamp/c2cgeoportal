Introduction
============

Fanstatic is a small but powerful framework for the automatic
publication of resources on a web page. Think Javascript and CSS. It
just serves static content, but it does it really well.

Can you use it in your project? If you use Python_, yes: Fanstatic is
web-framework agnostic, and will work with any web framework that
supports WSGI_. Fanstatic is issued under the BSD license.

.. _Python: http://www.python.org

.. _WSGI: http://wsgi.org/wsgi/

Why would you need something like Fanstatic? Can't you just add your
static resources to some statically served directory and forget about
them?  For small projects this is certainly sufficient. But so much
more is possible and useful in this modern Javascript-heavy
world. Fanstatic is able to offer a lot of powerful features for
projects both small and large.

Fanstatic has a lot of cool features:

Always the right resources
--------------------------

* **Import Javascript as easily as Python**: Javascript dependencies
  are a Python import statement away. Importing Python code is easy,
  why should it be harder to import Javascript code?

* **Depend in the right place**: do you have a lot of server-side code
  that assembles a web page? Want your datetime widget to pull in a
  datetime Javascript library, but only when that widget is on the
  page? Fanstatic lets you do that with one line of Python code.

* **Dependency tracking**: use a Javascript or CSS file that uses another
  one that in turn uses another one? Fanstatic knows about
  dependencies and will make sure all dependencies will appear on your
  page automatically. Have minified or rolled up versions available?
  Fanstatic can automatically serve those too.

* **Declare dependencies**: want to publish your own Javascript
  library?  Have your own CSS? Does it depend on other stuff?
  Fanstatic lets you declare dependencies with a few lines of Python
  code.

Optimization
------------

* **Serve the right version**: have alternative versions of your
  resource available? Want to serve minified versions of your
  Javascript during deployment? Debug versions during development?
  It's one configuration option away.

* **Bundle up resources**: roll up multiple resources into one and
  serve the combined resource to optimize page load time. Bundled
  resources can be generated automatically, or can automatically
  served when available.

* **Optimize load times**: Fanstatic knows about tricks to optimize
  the load time of your Javascript, for instance by including
  ``script`` tags at the bottom of your web page instead of in the
  ``head`` section.

Smart Caching
-------------

* **Infinite caching**: Fanstatic can publish static resources on
  unique URLs, so that the cache duration can be set to infinity. This
  means that browsers will hold on to your static resources: web
  server only gets that resource request once per user and no more. If
  a front-end in cache is in use, you reduce that to once per
  resource; the cache will handle all other hits.

* **Automatic deployment cache invalidation**: Fanstatic can
  automatically update all your resource URLs if new versions of
  resources are released in an application update. No longer do you
  need to instruct your user to use shift-reload in their application
  to refresh their resources.

* **Automatic development cache invalidation**: you can instruct
  Fanstatic to run in development mode. It will automatically use new
  URLs whenever you change your code now. No longer do you as a
  developer need to do shift-reload whenever you change a resource;
  just reload the page.

Powerful Deployment
-------------------

* **Automated deployment**: no longer do you need to tell people in
  separate instructions to publish Javascript libraries on a certain
  URL: Fanstatic can publish these for you automatically and
  transparently.

* **Pre-packaged libraries**: A lot of pre-packaged Javascript
  libraries are available on the PyPI and are maintained by the
  Fanstatic community. This can be installed into your project right
  away using easy_install, pip or buildout. No more complicated
  installation instructions, just reuse a Javascript library like you
  reuse Python libraries.

Compatible
----------

* **Fits your web framework**: Fanstatic integrates with any WSGI-compliant
  Python web framework.

* **Roll your own**: Not happy with the details of how Fanstatic
  works?  We've already split the Fanstatic WSGI component into
  separately usable components so you can mix and match and roll your
  own.
