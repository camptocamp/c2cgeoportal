# Developing

To develop in the admin interface read the related
[README](https://github.com/camptocamp/c2cgeoportal/blob/master/admin/README.md).

To develop in the geoportal part you should
[create a new application](https://camptocamp.github.io/c2cgeoportal/master/integrator/create_application.html),
Then have a look on the
[application debugging](https://camptocamp.github.io/c2cgeoportal/master/developer/debugging.html)
to be able to have your checkouted code running in the application.

## Pre-commit

Install the pre-commit hooks with::

```shell
pip install pre-commit
pre-commit install --allow-missing-config
```

Don't worry about the time take on the first run

Careful: If the pre-commit fail the commit will be aborted.

Commit without pre-commit

```shell
git commit (-n|--no-verify)
```

More information on [pre-commit](https://pre-commit.com/).
