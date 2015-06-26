Gatling tests
=============

`The tool <http://gatling.io>`_.

Gatling scripts:
 * ``geomapfish.Basic``: A small test on the application, create to for a performance test (without print)
 * ``geomapfish.Headers``: Test that all the headers will works
 * ``geomapfish.Layers``: Test all the layers at all resolutions
 * ``geomapfish.Test``: Test that a set of sits will be OK

Utility scripts:
 * ``get_layer.py``: used to get the layer configuration for ``Basic`` script (and ``Layers``) from the database
 * ``create_project.py``: used to create a great set of sites
