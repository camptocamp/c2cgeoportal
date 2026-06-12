# Agent Guidelines

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

## Headers configuration

When adding a new backend service/route that uses `set_common_headers(..., "<service>", ...)`:

- Add the corresponding key in `geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/geoportal/vars.yaml` under `headers`.
- Add the same key in `geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/geoportal/CONST_vars.yaml` under `headers`.
- Update `geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/geoportal/CONST_config-schema.yaml` to allow this `headers.<service>` entry.
- Add `headers.<service>.headers` in `geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/geoportal/vars.yaml` `update_paths` so values are inherited from `CONST_vars.yaml`.

This keeps generated projects consistent and allows CORS/cache header configuration for the service.

## Settings schema configuration

When adding backend runtime settings:

- Prefer nested settings maps (example: `user_settings.max_payload_size` should be configured as `user_settings: { max_payload_size: ... }`).
- Define defaults in `geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/geoportal/CONST_vars.yaml` close to related settings.
- Update `geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/geoportal/CONST_config-schema.yaml` accordingly.
- Validate settings type/shape in code and return an internal server error for invalid server configuration.

## Vars scaffolds overview

How the scaffolded configuration files work together:

- `geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/geoportal/CONST_vars.yaml` is the source of default values (referred by the `extends` field of the `vars.yaml` file).
- `geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/geoportal/vars.yaml` extends those defaults and should usually contain only project overrides.
- `geoportal/c2cgeoportal_geoportal/scaffolds/update/{{cookiecutter.project}}/geoportal/CONST_config-schema.yaml` validates the final merged config.

When adding new config entries, keep all three in sync:

- Add defaults in `CONST_vars.yaml`.
- Add schema support in `CONST_config-schema.yaml`.
- If the value should be inherited by generated projects through the create scaffold, add the relevant path in `create/.../vars.yaml` `update_paths`.

## Branch naming

Branch names must follow this format:

`<short-description>(-<issue>)?`

- `short-description` should briefly describe the change (kebab-case).
- `issue` is optional, and when present should be appended as a suffix (for example: `GSGMF-124`).
- Do not use unrelated prefixes such as release branch names when they are not part of the short description.
