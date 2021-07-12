# QGIS Docker image for GeoMapFish

Based on https://github.com/camptocamp/docker-qgis-server

## Configuration

Expect a geomapfish.yaml configuration file for the geomapfish_qgisserver plugin.

Example configuration file:

```yaml
vars:
    schema: main,
    schema_static: main_static,
    sqlalchemy_slave.url: 'postgresql://www-data:www-data@db:5432/geomapfish_tests',
    srid: 2056
```

Plugin configuration file path is given by `GEOMAPFISH_CONFIG` environment variable and default to `/etc/qgisserver/geomapfish.yaml`.

### Serving only one QGIS project

Require this environment variable:

- GEOMAPFISH_OGCSERVER: Name of `c2cgeoportal_commons.models.main.OGCServer` to serve.

Service will load QGIS project file using environment variable QGIS_PROJECT_FILE that default to `/etc/qgisserver/project.qgs`.

### Serving multiple QGIS projects

Require this environment variable:

- GEOMAPFISH_ACCESSCONTROL_CONFIG: Path to configuration file for mapping between GMF OGC servers QGIS project files.

Example multiple QGIS projects mapping:

```yaml
map_config:
  qgsproject1:
    ogc_server: qgisserver1
  qgsproject2:
    ogc_server: qgisserver2
```

## Prepare the tests

This target is a local target calling necessary root Makefile targets to ease development.

Build:

- QGIS Docker image with `geomapfish_qgisserver` plugin
- Plugin configuration file for tests (`tests/geomapfish.yaml`)

```bash
make prepare_tests
```

## Run the tests:

Build the tests docker image with tests and required dependencies and run tests.

```bash
make tests
```
