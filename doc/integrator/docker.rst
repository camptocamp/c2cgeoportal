.. _integrator_docker:

Use Docker to deploy your application
=====================================

Architecture schema
-------------------

For OpenShift projects:

.. mermaid::

    graph LR

        client(Web client);

        k8s[Kubernetes routing];
        geoportal[GeoMapFish server<br>camptocamp/geomapfishapp-geoportal];
        tcc[TileCloud-chain<br>camptocamp/tilecloud-chain];
        tccs[TileCloud-chain slave<br>camptocamp/tilecloud-chain];
        mapserver[MapServer<br>camptocamp/mapserver<br>or/and<br>camptocamp/qgis-server];
        tinyows[tinyows];
        print[Mapfist Print<br>camptocamp/mapfish-print];
        alembic[GeoMapFish alembic<br>camptocamp/geomapfishapp-geoportal<br>minor database upgrades];
        config[Project config<br>camtocamp/%project%-config<br>provides the config for all other containers];
        tools[GeoMapFish tools<br>camptocamp/geomapfishapp-tools];

        redis[(Redis)];
        redis:::data;


        postgres[(Postgres)];
        postgres:::data;
        storage[(Object staorage)];
        storage:::data;

        client ==> k8s;
        k8s ==> geoportal;
        k8s ==> tcc;
        geoportal --> tinyows;
        geoportal ==> mapserver;
        geoportal -. cache, broadcast .-> redis;
        geoportal -.-> postgres;
        geoportal -. raster data .-> storage;
        tcc -- on the fly --> mapserver;
        tccs -- pregenertation --> mapserver;
        tcc -. queue .-> redis;
        tccs -. queue .-> redis;
        tcc -. tiles .-> storage;
        tccs -. tiles .-> storage;
        geoportal --> print;
        print --> geoportal;
        alembic -.-> postgres;
        mapserver -.-> postgres;
        mapserver -.-> storage;
        tinyows -.-> postgres;

        classDef data fill:#5ba6ff,color:black;

For standalone projects:

.. mermaid::

    graph LR

        client(Web client);

        apache[Apache];
        subgraph Project composition
        haproxy[haproxy];
        geoportal[GeoMapFish server<br>camptocamp/geomapfishapp-geoportal];
        tcc[TileCloud-chain<br>camptocamp/tilecloud-chain];
        tccs[TileCloud-chain slave<br>camptocamp/tilecloud-chain];
        mapserver[MapServer<br>camptocamp/mapserver<br>or/and<br>camptocamp/qgis-server];
        tinyows[tinyows];
        print[Mapfist Print<br>camptocamp/mapfish-print];
        alembic[GeoMapFish alembic<br>camptocamp/geomapfishapp-geoportal<br>minor database upgrades];
        config[Project config<br>camtocamp/%project%-config<br>provides the config for all other containers];
        tools[GeoMapFish tools<br>camptocamp/geomapfishapp-tools];

        redis[(Redis)];
        redis:::data;
        end

        subgraph Second project composition
        haproxy2[haproxy];
        end

        postgres[(Postgres)];
        postgres:::data;
        storage[(File system)];
        storage:::data;

        client ==> apache;
        apache ==> haproxy;
        apache ==> haproxy2;
        haproxy ==> geoportal;
        haproxy ==> tcc;
        geoportal --> tinyows;
        geoportal ==> mapserver;
        geoportal -. cache, broadcast .-> redis;
        geoportal -.-> postgres;
        geoportal -. raster data .-> storage;
        tcc -- on the fly --> mapserver;
        tccs -- pregenertation --> mapserver;
        tcc -. queue .-> redis;
        tccs -. queue .-> redis;
        tcc -. tiles .-> storage;
        tccs -. tiles .-> storage;
        geoportal --> print;
        print --> geoportal;
        alembic -.-> postgres;
        mapserver -.-> postgres;
        mapserver -.-> storage;
        tinyows -.-> postgres;

        classDef data fill:#5ba6ff,color:black;

Docker Images
-------------

When you build your application, the following images will be generated:

* ``camptocamp/<package>_geoportal:latest``
* ``camptocamp/<package>_config:latest``

The tag is by default ``latest``, but you can change it by setting the ``DOCKER_TAG`` Makefile variable.


Docker compose files
--------------------

* ``docker-compose.yaml``: The main file that describes the composition.
* ``docker-compose-lib.yaml``: Provideis the base description of Geomapfish Docker services.
* ``.env``: Generated from the env files; contains the environment variables used by the composition.
* ``docker-compose.override[.sample].yaml``: Some rules for debuggung.
* ``.env``: The variable used in the compose files.


Run the developer composition
-----------------------------

.. prompt:: bash

   docker-compose up -d

You can then access your application with `https://localhost:8484/ <https://localhost:8484/>`_.


Clean
-----

Docker does not clean anything automatically, in particular it does not clean any images,
therefore disk space may become problematic after a certain number of builds.
You can use the following commands to manually remove Docker files.

Use ``docker system prune`` to clean files; you can add the ``--all`` option to do a deeper clean.


Environment variables
---------------------

The GeoMapFish containers can be customized with some environment variables:

Config:

 * ``VISIBLE_WEB_HOST``: The web host visible by the browser e.g.: 'example.com'.
 * ``VISIBLE_ENTRY_POINT``: The web path visible by the browser e.g.: '/main/', default to '/'.
 * ``PGSCHEMA``: The postgres schema, used by MapServer.
 * ``GEOPORTAL_INTERNAL_URL``: Used by the print in non mutualize mode.
 * ``TILECLOUDCHAIN_INTERNAL_URL``: Used by the print in non mutualize mode.
 * ``ST_JOIN``: Can be ``ST_Collect`` (default) or ``ST_Union``, ``ST_Collect`` is better for performance but
   does not support restriction area intersection.

Geoportal:

 * ``VISIBLE_ENTRY_POINT``: The web path visible by the browser e.g.: '/main/', default to '/'.
 * ``PGSCHEMA``: The postgres schema, used by MapServer.
 * ``AUTHTKT_TIMEOUT``: See: :ref:`integrator_authentication`.
 * ``AUTHTKT_REISSUE_TIME``: See: :ref:`integrator_authentication`.
 * ``AUTHTKT_MAXAGE``: See: :ref:`integrator_authentication`.
 * ``AUTHTKT_SECRET``: See: :ref:`integrator_authentication`.
 * ``AUTHTKT_COOKIENAME``: See: :ref:`integrator_authentication`.
 * ``AUTHTKT_HTTP_ONLY``: See: :ref:`integrator_authentication`.
 * ``AUTHTKT_SECURE``: See: :ref:`integrator_authentication`.
 * ``AUTHTKT_SAMESITE``: See: :ref:`integrator_authentication`.
 * ``BASICAUTH``: See: :ref:`integrator_authentication`.
 * ``LOG_TYPE``: Should be 'console' with Docker Compose and 'json' with OpenShift.
 * ``LOG_LEVEL``: Log level for your application, default to ``INFO``, can be
   ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL`` or ``NOTSET``,
   see also the ``production.ini`` file and the
   `logging documentation <https://docs.pylonsproject.org/projects/pyramid/en/1.5-branch/narr/logging.html>`_.
 * ``C2CGEOPORTAL_LOG_LEVEL``: Log level for all c2cgeoportal modules, default to ``WARN``.
 * ``C2CWSGIUTILS_LOG_LEVEL``: Log level for c2cwsgiutils, default to ``INFO``.
 * ``GUNICORN_LOG_LEVEL``: Log level for Gunicorn, default to ``INFO``.
 * ``SQL_LOG_LEVEL``: Log level for the SQLAlchemy engine``, default to ``WARN``.
 * ``DOGPILECACHE_LOG_LEVEL``: Log level for Dogpile cache, default to ``INFO``.
 * ``OTHER_LOG_LEVEL``: Log level for other modules, default to ``WARN``.
 * ``C2CGEOPORTAL_THEME_TIMEOUT``: Timeout in seconds used in requests on OGC servers during themes
   generation, default to ``300``.

QGIS server:

 * ``GEOMAPFISH_CONFIG``: The GeoMapFish config file, default to ``/etc/qgisserver/geomapfish.yaml``.
 * ``GEOMAPFISH_OGCSERVER``: The OGC server name in single QGIS project mode.
 * ``GEOMAPFISH_ACCESSCONTROL_CONFIG``: The access control config file for multi QGIS project mode.
 * ``GEOMAPFISH_POSITION``: The plugin position, default to ``100``.
 * ``LOG_LEVEL``: Log level for the GeoMapFish plugins, see also the ``logging.ini`` file.
 * ``C2CGEOPORTAL_LOG_LEVEL``: Log level for all c2cgeoportal modules, default to ``INFO``.
 * ``C2CWSGIUTILS_LOG_LEVEL``: Log level for c2cwsgiutils, default to ``INFO``.
 * ``SQL_LOG_LEVEL``: Log level for the SQLAlchemy engine``, default to ``WARN``.
 * ``OTHER_LOG_LEVEL``: Log level for other modules, default to ``WARN``.
 * ``QGIS_SERVER_LOG_LEVEL``: Qgis server log level, default to ``2``, ``0`` for verbose.
 * `Other QGIS server environment variables
   <https://docs.qgis.org/testing/en/docs/user_manual/working_with_ogc/server/config.html>`_.
 * ``CPL_VSIL_CURL_USE_CACHE``: GDAL option, default to ``TRUE``.
 * ``CPL_VSIL_CURL_CACHE_SIZE``: GDAL option, default to ``128000000``.
 * ``CPL_VSIL_CURL_USE_HEAD``: GDAL option, default to ``FALSE``.
 * ``GDAL_DISABLE_READDIR_ON_OPEN``: GDAL option, default to ``TRUE``.
 * `Other GDAL environment variables
   <https://gdal.org/user/configoptions.html#list-of-configuration-options-and-where-they-apply>`_.
