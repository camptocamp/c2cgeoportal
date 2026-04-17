## QGIS versions

The QGIS version appears in multiple places and all of them should be coherent:

- In `.github/workflows/main.yaml` the default version is specified when we build the QGIS image.
- In `.github/workflows/qgis.yaml` all the supported versions are listed in:
  - `main` `matrix`.
  - `main` `outputs`.
  - `success` first `steps`.
- In `geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/env.default` we should have the default version.
- In `.github/publish.yaml`, also the version for version `2.7` and `2.8`; see `.github/workflows/rebuild-qgis-*`.

## Bash

Use the long parameter names for clarity and maintainability.

## Tests

The new functionalities should be reasonably tested in the `*/tests/` folder or in `ci/test-app`.
