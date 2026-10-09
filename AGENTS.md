# Agent Guidelines

## QGIS versions

The QGIS version appears in multiple places and all of them should be coherent:

- In `.github/workflows/main.yaml` the default version is specified when we build the QGIS image.
- In `.github/workflows/qgis.yaml` all the supported versions are listed in:
  - `main` `matrix`.
  - `main` `outputs`.
  - `success` first `steps`.
- In `geoportal/c2cgeoportal_geoportal/scaffolds/create/{{cookiecutter.project}}/env.default` we should have the default version.
- In `.github/publish.yaml`, also the QGIS tags for the supported versions.

## Version lifecycle

The version lifecycle involves the linked repositories `ngeo`, `c2cgeoportal`, `demo_geomapfish` and
`argocd-gs-gmf-apps`; when a version is added, all of them should be kept consistent.
The detailed commands are in `doc/developer/build_release.rst`.

### Create the stabilization branch `<version>` from `master`

- Push the branch: `git push origin origin/master:refs/heads/<version>`.
- On the new branch:
  - Set `MAIN_BRANCH: '<version>'` in `.github/workflows/main.yaml` and `.github/workflows/qgis.yaml`.
  - Remove the workflows that only make sense on the default branch (`ngeo-*.yaml`, `rebuild-*.yaml`, ...).
  - Set `"ngeo": "version-<version>-latest"` in `geoportal/package.json` and regenerate
    `package-lock.json` with the `npm-lock` pre-commit hook, in a `setup-<version>` pull request.
  - Pull the Transifex branch resources
    (`tx pull --source --branch=<version> --force --resources=...` and the translations).
- The branch protection is automatically applied by the repository rulesets, they match the
  `refs/heads/[0-9].[0-9]` branches.
- The demo branch (`prod-<version>`) and the argocd application (`add-demo-<version>`) are managed in
  `demo_geomapfish` and `argocd-gs-gmf-apps`.

### Start the next version `<version + 1>` on `master`

In a `start-<version + 1>` pull request:

- Set `MAJOR_VERSION: '<version + 1>'` in `.github/workflows/main.yaml` and `.github/workflows/qgis.yaml`.
- Add the `.github/workflows/ngeo-<version>.yaml` maintenance workflow, adapted from the previous one
  (`repository_dispatch: ngeo_<version>_updated`, `MAIN_BRANCH`/`MAJOR_VERSION`, `QGIS_VERSION`, the
  `ci/test-upgrade` steps). It updates ngeo, the change log and the version on the stabilization branch
  and republishes the images with
  `tag-publish --type=rebuild --version=<version> --docker-versions=...`.
- Add `| <version> | To be defined |` in `SECURITY.md`; GHCI keeps the Renovate `baseBranchPatterns` and
  the `backport <version>` labels up to date from this file.
- Update the defaults: `Makefile` (`MAJOR_VERSION`, `MAJOR_MINOR_VERSION`, `VERSION`),
  `scripts/get-version` (default `MAJOR_VERSION`) and `scripts/updated_version` (threshold).
- Update `ci/test-upgrade`: rename the current development version test to `<version + 1>` and add the
  migration test from `<version>` (with the used image tag) and its case and cleanup; add the
  corresponding step in `.github/workflows/main.yaml`.
- Push the Transifex resources of the next version (`tx push --branch=<version + 1> ...`).

### On release `<version>.0`

- Reset `CHANGELOG.md` and `ci/changelog.yaml` on the stabilization branch.
- Tag the release and publish it.

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
