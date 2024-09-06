.. _integrator_objectstorage:

Working with Object storage (like S3)
=====================================


Prepare files
-------------

We can prepare a GeoTIFF for the Cloud, see the `COG file format <https://www.cogeo.org/>`_
and the `GDAL output driver options <https://gdal.org/drivers/raster/cog.html>`_.


Generalities
------------

In this section, we explain how to use the S3-like storage from Exoscale,
or the blob container from Azure.

First of all, you should set the following variables on the desired env file:

For Exoscale:

* ``AWS_ACCESS_KEY_ID``: The project access key.
* ``AWS_SECRET_ACCESS_KEY``: The project secret key.
* ``AWS_DEFAULT_REGION=ch-dk-2``: The region used by Exoscale.
* ``AWS_S3_ENDPOINT=sos-ch-dk-2.exo.io``: The endpoint used by Exoscale.

For Azure connection string:

* ``AZURE_STORAGE_CONNECTION_STRING``: The connection string.

For Azure blob container URL:

* ``AZURE_STORAGE_BLOB_CONTAINER_URL``: The blob container URL.

For better performance, you should furthermore also set the following variables:

* ``CPL_VSIL_CURL_USE_CACHE=TRUE``
* ``CPL_VSIL_CURL_CACHE_SIZE=128000000``
* ``CPL_VSIL_CURL_USE_HEAD=FALSE``
* ``GDAL_DISABLE_READDIR_ON_OPEN=TRUE``


Exoscale:

Use the aws client to list the files:

.. prompt:: bash

   aws --endpoint-url https://sos-ch-dk-2.exo.io/ --region ch-dk-2 \
        s3 ls s3://<bucket>/<folder>


Create the vrt file for a raster layer:

.. prompt:: bash

   docker-compose exec geoportal bash -c \
        'gdalbuildvrt /vsis3/<bucket>/<folder>/index.vrt \
        $(list4vrt <bucket> <folder>/ .tif)'

Azure connection string:

Use list the container:

.. prompt:: bash

   docker-compose exec geoportal azure --list-container

Use list the files:

.. prompt:: bash

   docker-compose exec geoportal azure --container=<container> --list ''

Create the vrt file for a raster layer:

.. prompt:: bash

   docker-compose exec geoportal azure --container=<container> --vrt <folder>/ .tiff

Azure blob container URL:

Use list the files:

.. prompt:: bash

   docker compose exec geoportal azure --list ''

Create the vrt file for a raster layer:

.. prompt:: bash

   docker compose exec geoportal azure --vrt <folder>/ .tiff

MapServer
---------

Create the shape index file for a raster layer:

Exoscale:

.. prompt:: bash

   docker-compose exec geoportal bash -c \
        'gdaltindex mapserver/index.shp $( \
            aws --endpoint-url http://${AWS_S3_ENDPOINT} \
                --region ${AWS_DEFAULT_REGION} \
                s3 ls s3://<bucket>/<folder>/ | \
            grep tif$ | \
            awk '"'"'{print "/vsis3/<bucket>/<folder>/"$4}'"'"' \
        )'
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.shp mapserver/
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.shx mapserver/
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.dbf mapserver/
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.prj mapserver/

Azure connection string:

.. prompt:: bash

   docker-compose exec geoportal rm index.shp
   docker-compose exec geoportal rm index.shx
   docker-compose exec geoportal rm index.dbf
   docker-compose exec geoportal rm index.prj
   docker-compose exec geoportal bash -c \
        'gdaltindex mapserver/index.shp $( \
            azure --container=<container> --list <folder>/ | \
            grep tiff$ | \
            awk '"'"'{print "/vsiaz/<container>/"$1}'"'"' \
        )'
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.shp mapserver/<set>.shp
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.shx mapserver/<set>.shx
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.dbf mapserver/<set>.dbf
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.prj mapserver/<set>.prj

Azure blob container URL:

.. prompt:: bash

   docker compose exec geoportal rm index.shp
   docker compose exec geoportal rm index.shx
   docker compose exec geoportal rm index.dbf
   docker compose exec geoportal rm index.prj
   docker compose exec geoportal bash -c \
        'gdaltindex mapserver/index.shp $( \
            azure --list <folder>/ | \
            grep tiff$ | \
            awk '"'"'{print "/vsiaz/<container>/"$1}'"'"' \
        )'
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.shp mapserver/<set>.shp
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.shx mapserver/<set>.shx
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.dbf mapserver/<set>.dbf
    docker cp <docker_compose_project_name>_geoportal_1:/app/index.prj mapserver/<set>.prj

Add the following config in the ``mapserver/mapserver.map.tmpl`` file:

.. code::

   CONFIG "CPL_VSIL_CURL_USE_CACHE" "TRUE"
   CONFIG "CPL_VSIL_CURL_CACHE_SIZE" "128000000"
   CONFIG "CPL_VSIL_CURL_USE_HEAD" "FALSE"
   CONFIG "GDAL_DISABLE_READDIR_ON_OPEN" "TRUE"

Exoscale:

.. code::

   CONFIG "AWS_ACCESS_KEY_ID" "${AWS_ACCESS_KEY_ID}"
   CONFIG "AWS_SECRET_ACCESS_KEY" "${AWS_SECRET_ACCESS_KEY}"
   CONFIG "AWS_DEFAULT_REGION" "${AWS_DEFAULT_REGION}"
   CONFIG "AWS_S3_ENDPOINT" "${AWS_S3_ENDPOINT}"

Azure connection string:

.. code::

   ${DISABLE_LOCAL} CONFIG "AZURE_STORAGE_CONNECTION_STRING" "${AZURE_STORAGE_CONNECTION_STRING}"
   ${DISABLE_MUTUALIZE} CONFIG "AZURE_STORAGE_ACCOUNT" "${AZURE_STORAGE_ACCOUNT}"

Azure blob container URL:

.. code::

   ${DISABLE_LOCAL} CONFIG "AZURE_STORAGE_ACCOUNT" "${AZURE_STORAGE_ACCOUNT}"
   ${DISABLE_LOCAL} CONFIG "AZURE_STORAGE_SAS_TOKEN" "${AZURE_STORAGE_SAS_TOKEN}"
   ${DISABLE_MUTUALIZE} CONFIG "AZURE_STORAGE_ACCOUNT" "${AZURE_STORAGE_ACCOUNT}"

Use the shape index in the layer:

.. code::

   TYPE RASTER
   STATUS ON
   PROCESSING "RESAMPLE=AVERAGE"
   CONNECTIONTYPE OGR
   TILEINDEX "index.shp"
   TILEITEM "LOCATION"

Add a vector layer for the object storage:

.. code::

   CONNECTIONTYPE OGR
   CONNECTION "${RASTER_BASE_PATH}<path>/<name>.shp"
   DATA "<name>"

`Some more information <https://github.com/mapserver/mapserver/wiki/Render-images-straight-out-of-S3-with-the-vsicurl-driver>`_

.. note::

   If you want to use different buckets or containers in different environments
   (such as integration / production), you should add an empty file named ``<tileindexbasename>.raster``
   (not ``<tileindexbasename>.shp.raster``) and a ``RASTER_BASE_PATH`` environment variable in your
   `env.project` file, then the base path will be replaced (same number of folders).
   The empty raster files are here just to find the files that should be managed.

   Example: `RASTER_BASE_PATH=/vsiaz/<container>/`


QGIS
----

Client
~~~~~~

The following environment variables should be defined (in the OS or in QGIS
(``Settings`` / ``Options...`` / ``System`` / ``Environment``)):

Exoscale:

* ``AWS_ACCESS_KEY_ID``: The project access key.
* ``AWS_SECRET_ACCESS_KEY``: The project secret key.
* ``AWS_DEFAULT_REGION=ch-dk-2``: The region used by Exoscale.
* ``AWS_S3_ENDPOINT=sos-ch-dk-2.exo.io``: The endpoint used by Exoscale.

Azure connection string:

* ``AZURE_STORAGE_CONNECTION_STRING``: The connection string.

Azure blob container URL:

* ``AZURE_STORAGE_ACCOUNT``: The account name.
* ``AZURE_STORAGE_SAS_TOKEN``: The SAS token.

On Windows also add:

* ``GDAL_HTTP_UNSAFESSL=YES``

Then you can add a raster layer with:

* Open from the menu ``Layer`` / ``Add Layer`` / ``Add Raster Layer``.
* Section: ``Raster``.
* ``Source type``: ``Protocole: HTTP(S), cloud, etc.``.
* ``Type``: ``AWS S3`` or ``Microsoft Azure Blob``.
* ``Bucket or container``: <bucket> or <container>.
* ``Object key``: <folder>/index.vrt.

You can add a vector layer in an analogous manner.

Server
~~~~~~

Fill the required environment variables.

Exoscale:

* ``AWS_ACCESS_KEY_ID``: The project access key.
* ``AWS_SECRET_ACCESS_KEY``: The project secret key.
* ``AWS_DEFAULT_REGION=ch-dk-2``: Should already be in your env.project.
* ``AWS_S3_ENDPOINT=sos-ch-dk-2.exo.io``: Should already be in your env.project.

Azure connection string:

* ``AZURE_STORAGE_CONNECTION_STRING``: The connection string.

Azure blob container URL:

* ``AZURE_STORAGE_ACCOUNT``: The account name.
* ``AZURE_STORAGE_SAS_TOKEN``: The SAS token.

For Azure AKS the access should be given by the AzureAssignedIdentity in Kubernetes,

.. note::

   If you want to use different buckets or containers in different environments
   (such as integration / production), you should add an empty file names
   ``<name>.qgs.raster`` or ``<name>.qgz.raster``
   and a ``RASTER_BASE_PATH`` environment variable in your
   config container, then the base path will be replaced (same number of folder).
   The empty raster files are here just to find the files that should be managed.
