Developing Fanstatic
====================

You want to contribute to Fanstatic? Great!

Please talk to us our on our :ref:`mailing list <mailing list>` about
your plans!

Sources
-------

Fanstatic's source code is maintained on bitbucket:
http://bitbucket.org/fanstatic

You can check out fanstatic using `Mercurial`_ (hg); see the bitbucket_
documentation for more information as well.

.. _`Mercurial`: http://mercurial.selenic.com/

.. _`bitbucket`: http://bitbucket.org

Feel free to fork Fanstatic on bitbucket if you want to hack on it,
and send us a pull request when you want us to merge your
improvements.

Development install of Fanstatic
--------------------------------

Fanstatic requires Python 2.6. We believe that the Fanstatic
development installation is a good example of how to install a lot of
useful tools into a project's sandbox automatically; read on.

To install Fanstatic for development, first check it out, then run the
buildout::

 $ python bootstrap.py -d
 $ bin/buildout

This uses Buildout_. The buildout process will download and install
all dependencies for Fanstatic, including development tools.

Don't worry, that's all you need to know about buildout to get going
-- you only need to run ``bin/buildout`` again if something changes in
Fanstatic's ``buildout.cfg`` or ``setup.py``.

The ``-d`` option is to instruct buildout to use Distribute_ instead
of Setuptools_ and is optional.

.. _Buildout: http://buildout.org

.. _Distribute: http://packages.python.org/distribute/

.. _Setuptools: http://pypi.python.org/pypi/setuptools

Tests
-----

To run the tests::

  $ bin/py.test

This uses `py.test`_. We love tests, so please write some if you want
to contribute. There are many examples of tests in the ``test_*.py``
modules.

.. _`py.test`: http://pytest.org/

Test coverage
-------------

To get a test coverage report::

  $ bin/py.test --cov fanstatic

To get a report with more details::

   bin/py.test --cov-report html --cov fanstatic

The results will be stored in a subdirectory ``htmlcov``. You can point
a web browser to its ``index.html`` to get a detailed coverage report.

pyflakes
--------

To run pyflakes_, you can type::

  $ bin/pyflakes fanstatic

.. _pyflakes: http://divmod.org/trac/wiki/DivmodPyflakes


.. _buildbot:

Buildbot
--------

The fanstatic tests are run daily on the `THA buildbot <http://dev.thehealthagency.com/buildbot/>`_.
We are working on a pretty overview of the buildbot status.
For now, just search for ``fanstatic`` in the `list of projects <http://dev.thehealthagency.com/buildbot/one_box_per_builder>`_.

The configuration of the buildbot lives on
svn+ssh://svn.zope.org/repos/main/Sandbox/janjaapdriessen/buildbot

Building the documentation
--------------------------

To build the documentation using Sphinx_::

  $ bin/sphinxbuilder

.. _Sphinx: http://sphinx.pocoo.org/

If you use this command, all the dependencies will have been set up
for Sphinx so that the API documentation can be automatically
extracted from the Fanstatic source code. The docs source is in
``doc``, the built documentation will be available in
``doc/_build/html``.

Python with Fanstatic on the sys.path
-------------------------------------

It's often useful to have a project and its dependencies available for
import on a Python prompt for experimentation::

  $ bin/devpython

You can now import fanstatic::

  >>> import fanstatic

You can also run your own scripts with this custom interpreter if you
like::

  $ bin/devpython somescript.py

This can be useful for quick experimentation. When you want to use
Fanstatic in your own projects you would normally include it in your
project's ``setup.py`` dependencies instead.

Releases
--------

The buildout also installs `zest.releaser`_ which can be used to make
automatic releases to PyPI (using ``bin/fullrelease``).

.. _`zest.releaser`: http://pypi.python.org/pypi/zest.releaser

Pre-packaged libraries
----------------------

If you want to make an existing JS library into a fanstatic package, use the
fanstatic paster template from the :pypi:`fanstatictemplate` package.

The pre-packaged libraries live in the http://bitbucket.org/fanstatic account.

In order to add a new library, ask one of the fanstatic administrators to create
a repository for you. In the new repository, run :pypi:`fanstatictemplate` and
push your changes.

Register the newly created package on PyPI and add the fanstatic administrators
(currently `faassen`, `jw` and `janjaapdriessen`) as owners. After that, add
your library to the list of :ref:`packaged_libs`.
