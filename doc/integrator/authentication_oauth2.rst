OAuth2 with QGIS
~~~~~~~~~~~~~~~~

In the admin interface create an 'OAuth2 Client' with:

* ``Client ID`` as e.-g. 'qgis'
* fill the ``Secret``
* ``Redirect URI`` as 'http://127.0.0.1:7070/'

On QGIS:

* Add an ``Authentication``
* Set a ``Name``
* Set ``Authentication`` to ``OAuth2``
* Set ``Grant flow`` to ``Authentication code``
* Set ``Request URL`` to ``<geomapfish_base_url>/oauth/login``
* Set ``Token URL`` to ``<geomapfish_base_url>/oauth/token``
* Set ``Client ID`` to 'qgis'
* Set ``Client secret`` to the secret

.. note::

    For security reason a user can only have one active session per client.

    If you need to have more than one active session you should provide more than one client.
