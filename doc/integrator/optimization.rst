.. integrator.optimization:

Optimization
=============

Introduction
--------------

Optimization is important in all application. It depends strongly on 
the data and some others best practices. This document aims to present 
some of them.

Best practices are as important in Mapserver side as in data base side. Your 
data should be designed to improve performance, don't store unrequired column, 
add column which can help for data classification in MapServer, etc.

MapFile
--------

PostGIS layer
~~~~~~~~~~~~~

* CLOSE_CONNECTION parameter:

  In case you are using more than 2 postgis table, you should use::
	
	PROCESSING "CLOSE_CONNECTION=DEFER"

  parameter. This allows MapServer to keep connections to PostGIS database and improve 
  performance.

* SRID and Primary Key:

  Always add primary key and SRID in the DATA string, otherwise MapServer do two 
  extra queries to get the information::
	DATA "the_geom from the_table using unique gid using srid=4326"

Outputformat
~~~~~~~~~~~~~

Outputformat is really important as it can allow MapServer to decrease picture 
size from 500kb to 130kb. For some data, one can decrease number of colors to 256 
without quality loss in the final image. Here is an outputformat example to use 
in MapServer configuration file::
	OUTPUTFORMAT
	    NAME png
		DRIVER AGG/PNG
		MIMETYPE "image/png"
		IMAGEMODE RGBA
		EXTENSION "png"
		FORMATOPTION "INTERLACE=OFF"
		FORMATOPTION "QUANTIZE_DITHER=OFF"
		FORMATOPTION "QUANTIZE_FORCE=ON"
		FORMATOPTION "QUANTIZE_COLORS=256"
	END

The important part is the three QUANTIZE_* parameters in FORMATOPTION.

POSTGIS
--------

INDEX et CLUSTER
~~~~~~~~~~~~~~~~~

Indexes increase performance but you can improve it even more in your application by 
adding an index on a column. In geospatial applications, the column should be the geometry 
column::
	CREATE INDEX myTable_geom_idx ON mySchema.myTable USING gist(geom);
	CLUSTER myTable_geom_idx ON mySchema.myTable;


Others tips
------------

You can find more tips in MapServer documentation website : http://mapserver.org/optimization/mapfile.html
