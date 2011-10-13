Quickstart
==========

This quickstart will demonstrate how you can integrate Fanstatic with
a WSGI-based web application.

In this example, we will use Python to hook up Fanstatic to your WSGI
application, but you could also use a WSGI configuration framework
like `Paste Deploy`_. For more information about this, see :doc:`our
Paste Deploy documentation <paste_deploy>`.

.. _`Paste Deploy`: http://pythonpaste.org/deploy/

A simple WSGI application
-------------------------

A simple WSGI application will stand in for your web application::

    def app(environ, start_response):
        start_response('200 OK', [])
        return ['<html><head></head><body></body></html>']

As you can see, it simply produces the following web page, no
matter what kind of request it receives::

  <html><head></head><body></body></html>

You can also include some code to start and run the WSGI
application. Python includes ``wsgiref``, a WSGI server
implementation::

  if __name__ == '__main__':
      from wsgiref.simple_server import make_server
      server = make_server('127.0.0.1', 8080, app)
      server.serve_forever()

For real-world uses you would likely want to use a more capable WSGI
server, such as Paste Deploy as mentioned before, or for instance
mod_wsgi_.

.. _mod_wsgi: https://code.google.com/p/modwsgi/

Including resources without Fanstatic
-------------------------------------

Let's say we want to start using jQuery in this application. The way
to do this without Fanstatic would be:

* download jQuery somewhere and publish it somewhere as a static
  resource. Alternatively use a URL to jQuery already published
  somewhere on the web using a content distribution network (CDN).

* modify the ``<head>`` section of the HTML in your code to add a
  ``<script>`` tag that references jQuery, in all HTML pages that need
  jQuery.

This is fine for simple requirements, but gets hairy once you have a
lot of pages that need a variety of Javascript libraries (which may
change dynamically), or if you need a larger selection of Javascript
libraries with a more involved dependency structure. Soon you find
yourself juggling HTML templates with lots of ``<script>`` tags,
puzzling over what depends on what, and organizing a large variety of
static resources.

Including resources with Fanstatic
----------------------------------

How would we do this with Fanstatic? Like this::

    from js.jquery import jquery

    def app(environ, start_response):
        start_response('200 OK', [])
        jquery.need()
        return ['<html><head></head><body></body></html>']

You need to make sure that ``js.jquery`` is available in your
project using a familiar Python library installation system such as
`pip`_, `easy_install`_ or `buildout`_. This will automatically make
the Javascript code available on your system.

.. _pip: http://pip.openplans.org/

.. _easy_install: http://packages.python.org/distribute/easy_install.html

.. _buildout: http://buildout.org

Wrapping your app with Fanstatic
--------------------------------

To use Fanstatic, you need to configure your application so that
Fanstatic can do two things for you:

* automatically inject resource inclusion requirements (the
  ``<script>`` tag) into your web page.

* serve the static resources (such as jQuery.js) when a request to a
  resource is made.

Fanstatic provides a WSGI framework component called ``Fanstatic``
that does both of these things for you. Here is how you use it::

  from fanstatic import Fanstatic

  fanstatic_app = Fanstatic(app)

When you use ``fanstatic_app``, Fanstatic will take care of serving
static resources for you, and will include them on web pages when
needed. You can import and ``need`` resources all through your
application's code, and Fanstatic will make sure that they are served
correctly and that the right script tags appear on your web page.

If you used ``wsgiref`` for instance, this is what you'd write to use the
Fanstatic wrapped app::

  if __name__ == '__main__':
      from wsgiref.simple_server import make_server
      server = make_server('127.0.0.1', 8080, fanstatic_app)
      server.serve_forever()

The resulting HTML looks like this::

  <html>
    <head>
      <script type="text/javascript" src="/fanstatic/jquery/jquery.js"></script>
    </head>
    <body>
    </body>
  </html>

Now you're off and running with Fanstatic!
