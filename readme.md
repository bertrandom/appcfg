# appcfg

[![PyPI version fury.io](https://badge.fury.io/py/appcfg.svg)](https://pypi.python.org/pypi/appcfg/)
[![Build Status](https://travis-ci.com/bjoluc/appcfg.svg?branch=master)](https://travis-ci.com/bjoluc/appcfg)
[![codecov](https://codecov.io/gh/bjoluc/appcfg/branch/master/graph/badge.svg)](https://codecov.io/gh/bjoluc/appcfg)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/appcfg.svg)](https://pypi.python.org/pypi/appcfg/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Flexible hierarchic Python application configuration inspired by [node-config](https://github.com/lorenwest/node-config)

## Motivation

Applications (especially web services) often require certain configuration options to depend on the environment an application runs in (development, testing, production, etc.).
For instance, a database address config option may default to a local database server during development, a mock database server during testing, and yet another database server during production.
It may also need to be customizable via an environment variable.
`appcfg` approaches scenarios like this and, similar to [node-config](https://github.com/lorenwest/node-config) for Node.js, allows to specify default configuration options for various environments and optionally override them by custom environment variables.

## Getting Started

Let's start by installing `appcfg` with ```pip install appcfg[yaml]```, or simply ```pip install appcfg``` if you want to use the JSON format instead of YAML for config files.

In the top-level directory of your application (where the topmost `__init__.py` file is located), create a `config` directory.
If your application consists of a single Python file, just locate the `config` directory next to it.
Here's an example project tree that we will refer to in the rest of this section:

```diff
 ├── myproject
 │   ├── __init__.py
+│   ├── config
+|   |   └── ...
 |   ├── anothermodule.py
 │   └── myproject.py
 ├── tests
 │   ├── __init__.py
 │   └── test_myproject.py
```

Within the `config` directory, create a `default.yml` file (or `default.json`, if you prefer that).
This file will hold your default configuration.
In the database example from the previous section, `default.yml` might look like this:

```yaml
databases:
    mongo:
        host: localhost
        port: 27017
        user: myuser
        pass: mypassword
secrets:
    mysecret: secret
```

Within any module in the `myproject` package, we can now simply access that configuration as a `dict` object:

```python
from appcfg import get_config

config = get_config(__name__)
print(config["databases"]["mongo"]["host"])
```

`__name__` is passed to `get_config` so that it can infer the project root path where the `config` directory is located.
This way, `appcfg` can be used independently in multiple projects loaded at the same time, and projects can also retrieve one another's configuration.
For instance, in `test_myproject.py`, the configuration of `myproject` could be retrieved with `get_config("myproject")`.

## Environments

Let's add an override config file for production, `production.yml`:

```yaml
databases:
    mongo:
        host: mongodb
```

And one for testing, `test.yml`:

```yaml
databases:
    mongo:
        host: mock
secrets:
    mysecret: wellknown
```

By default, none of these config files will be used.
However, an environment can be specified by setting the `ENV` environment variable (alternatively, `PY_ENV` or `ENVIRONMENT` are also supported).
In this case, the configuration options from the corresponding config file will be merged into the ones from `default.yml`.
If, for instance, `ENV` is set to `production`, the config dict returned from `get_config()` will contain all the values from `default.yml`, but `config["databases"]["mongo"]["host"]` will be set to `mongodb` instead of `localhost`.
Similarly, with `ENV=test`, `config["databases"]["mongo"]["host"]` would be `mock` and, `config["secret"]["mysecret"]` would be `wellknown`.
In case `ENV` is set but no corresponding config file is found, `get_config()` returns the options from the `default` config file.

## Custom Environment Variables

Let's say, we want the database host, user, and password, and the secret to be customizable via additional environment variables.
This can be achieved by adding an `env-vars.yml` config file with the following contents:

```yaml
databases:
    mongo:
        host: MONGO_HOST
        user: MONGO_USER
        pass: MONGO_PASS
secrets:
    mysecret: MY_SECRET
```

This way, if one of the specified environment variables is set, it will override the corresponding field's value from any other configuration file.
Otherwise, that value is left untouched.
For instance, setting `MONGO_HOST=myhost` would result in `config["databases"]["mongo"]["host"]` to be `myhost`, ignoring `localhost` from `default.yml` or `mongodb` from `production.yml`.
Note that config values set via environment variables are always of type `str`, regardless of the overridden value's type.

## Tips and Tricks

### Environment Specification with pytest

You may wish to set `ENV=test` during unit tests without manually specifying it for every `pytest` invocation.
[pytest-env](https://github.com/MobileDynasty/pytest-env) can do the job for you if you specify

```ini
[pytest]
env =
    ENV=test
```

in your pytest configuration.

<!-- BEING API DOC -->

## API


### get_config

Returns a dict that contains the content of `default.json` or `default.yml` in the `config` directory within the root module's directory, inferred from `module_name`.


If an `ENV`, `PY_ENV`, or `ENVIRONMENT` variable is set (listed in the order of
precedence), and a config file with a base name corresponding to that variable's
value is found, the contents of that config file are merged into the default
configuration. Additionally, the environment variables specified in `env-vars.json`
or `env-vars.yml` override any other configuration when they are set.

If none of `ENV`, `PY_ENV`, or `ENVIRONMENT` is set, only the `default` config file
will be loaded and optionally be overridden by custom environment variables as
specified in the `env-vars` config file. The `ENV` values "dev" and "develop" map to
the `development.json` or `development.yml` config file.

**Arguments**:

- `module_name` (`str`): The name of the module (or any of its submodules) for which
  the configuration should be loaded. `__name__` can be used when `get_config()` is
  called from the Python project that contains the `config` directory. Note that
  `appcfg` requires the `config` directory to be a direct child of the top-level
  package directory, or, if not a package, the directory that contains the specified
  module.

- `cached` (`bool`): If `True` (the default), the configuration for each `config`
  directory will only be loaded once and the same dict object will be returned by
  every subsequent call to `get_config()`.


### get_env

If an `ENV`, `PY_ENV`, or `ENVIRONMENT` (listed in the order of precedence) environment variable is set, return the value of it. Otherwise, return "default".


Special cases:
  - "dev" and "develop" are mapped to "development"

<!-- END API DOC -->
