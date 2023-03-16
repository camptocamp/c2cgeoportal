# c2cgeoportal application

c2cgeoportal is the server part of [GeoMapFish](https://geomapfish.org/),
the client part is [ngeo](https://github.com/camptocamp/ngeo/).

Read the [Documentation](https://camptocamp.github.io/c2cgeoportal/master/).

Docker images:
[To build the project and more tools](https://hub.docker.com/r/camptocamp/geomapfish-tools),
[To config base image](https://hub.docker.com/r/camptocamp/geomapfish-config),
[Base image to run the project](https://hub.docker.com/r/camptocamp/geomapfishapp-geoportal),
[Default image to run the project](https://hub.docker.com/r/camptocamp/geomapfish),
[QGIS server with access control plugin](https://hub.docker.com/r/camptocamp/geomapfish-qgisserver).

Python packages:
[commons](https://pypi.org/project/c2cgeoportal-commons/),
[geoportal](https://pypi.org/project/c2cgeoportal-geoportal/),
[admin](https://pypi.org/project/c2cgeoportal-admin/).

[NPM package](https://www.npmjs.com/package/ngeo).

The [changelog](./CHANGELOG.md).

Resources managed by the user group community:

- [Geomapfish user-group website](https://geomapfish.org/)
- [Issue tracker (e.g. to ask for new feature)](https://github.com/camptocamp/GeoMapFish/issues)
- [Getting Started (quickly start a GeoMapFish)](https://github.com/geomapfish/getting_started)

## Contributing

Install the pre-commit hooks:

```bash
pip install pre-commit
pre-commit install --allow-missing-config
```
