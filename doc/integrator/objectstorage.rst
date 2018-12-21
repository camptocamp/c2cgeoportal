.. _integrator_objectstorage:

Working with Object storage (like S3)
=====================================

Generalities
------------

In this we will consider to use the S3-like from Exoscale.

First of all we should set the following variables on the ``geoportal``, ``config`` and ``qgisserver`` services.

* ``AWS_ACCESS_KEY_ID``: The project access key.
* ``AWS_SECRET_ACCESS_KEY``: The project secret key.
* ``AWS_DEFAULT_REGION=ch-dk-2``: The region used by Exoscale.
* ``AWS_S3_ENDPOINT=sos-ch-dk-2.exo.io``: The endpoint used by Exoscale.

For better performance, we should set the following variables on the ``geoportal`` and ``qgisserver`` services.

* ``CPL_VSIL_CURL_USE_CACHE=TRUE``
* ``CPL_VSIL_CURL_CACHE_SIZE=128000000``
* ``CPL_VSIL_CURL_USE_HEAD=FALSE``
* ``GDAL_DISABLE_READDIR_ON_OPEN=TRUE``


Use the aws client to list the files:

.. prompt:: bash

   aws --endpoint-url https://sos-ch-dk-2.exo.io/ --region ch-dk-2 s3 ls s3://<bucket>/<folder>


Create the vrt file for a raster layer:

.. prompt:: bash

   gdalbuildvrt `aws --endpoint-url https://sos-ch-dk-2.exo.io/ --region ch-dk-2 s3 ls \
        s3://<bucket>/<folder>/*.geotiff|awk '{print $4}'` s3://<bucket>/<folder>/index.vrt

MapServer
---------

Create the shape index file for a raster layer:

.. prompt:: bash

   gdaltindex mapserver/index.shp `aws --endpoint-url https://sos-ch-dk-2.exo.io/ --region ch-dk-2 s3 ls \
        s3://<bucket>/<folder>/*.geotiff|awk '{print $4}'`


Add the following config in the ``mapserver/mapserver.map.tmpl`` file:

.. code::

   CONFIG "CPL_VSIL_CURL_USE_CACHE" "TRUE"
   CONFIG "CPL_VSIL_CURL_CACHE_SIZE" "128000000"
   CONFIG "CPL_VSIL_CURL_USE_HEAD" "FALSE"
   CONFIG "GDAL_DISABLE_READDIR_ON_OPEN" "TRUE"

   CONFIG "AWS_ACCESS_KEY_ID" "${AWS_ACCESS_KEY_ID}"
   CONFIG "AWS_SECRET_ACCESS_KEY" "${AWS_SECRET_ACCESS_KEY}"
   CONFIG "AWS_DEFAULT_REGION" "${AWS_DEFAULT_REGION}"
   CONFIG "AWS_S3_ENDPOINT" "${AWS_S3_ENDPOINT}"

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
   CONNECTION "/vsis3/<bucket>/<path>/<name>.shp"
   DATA "<name>"

`Some more information <https://github.com/mapserver/mapserver/wiki/Render-images-straight-out-of-S3-with-the-vsicurl-driver>`_

QGIS client
-----------

Open settings, Option and define the following environment variables:

* ``AWS_ACCESS_KEY_ID``: The project access key.
* ``AWS_SECRET_ACCESS_KEY``: The project secret key.
* ``AWS_DEFAULT_REGION=ch-dk-2``: The region used by Exoscale.
* ``AWS_S3_ENDPOINT=sos-ch-dk-2.exo.io``: The endpoint used by Exoscale.

On Windows also add:

* ``GDAL_HTTP_UNSAFESSL=YES``

Then you can add a raster layer with:

* Open Data Source Manager,
* Raster,
* Protocol: HTTP(S), cloud, etc.,
* Type: AWS S3
* Bucket or container: <bucket>
* Object key: <folder>/index.vrt

You can add a vector layer in an analogous manner.
