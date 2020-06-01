from appcfg.util import (
    compile_env_vars_template,
    get_config_dir,
    get_environment,
    load_config_file,
    merge_configs,
    validate_env_vars_template,
)
from typing import Dict

# Map config directories to the corresponding config objects
_config_cache: Dict[str, dict] = {}


def _get_config(config_dir):
    """
    Given a config directory, assemble and return the corresponding configuration dict
    """
    config = load_config_file(config_dir, "default", strict=True)

    env = get_environment()
    if env != "default":
        override = load_config_file(config_dir, env)
        if override is not None:
            merge_configs(config, override)

    env_vars_override = load_config_file(config_dir, "env-vars")
    if env_vars_override is not None:
        validate_env_vars_template(env_vars_override)
        compile_env_vars_template(env_vars_override)
        merge_configs(config, env_vars_override)

    return config


# Public caching wrapper around _get_config
def get_config(module_name: str, cached=True):
    """
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
      the configuration should be loaded for. `__name__` can be used when `get_config()`
      is called from the Python project that contains the `config` directory. Note that
      `appcfg` requires the `config` directory to be a direct child of the top-level
      package directory, or, if not a package, the directory that contains the specified
      module.

    - `cached` (`bool`): If `True` (the default), the configuration for each `config`
      directory will only be loaded once and the same dict object will be returned by
      every subsequent call to `get_config()`.
    """
    config_dir = get_config_dir(module_name)
    if not cached:
        return _get_config(config_dir)
    else:
        if config_dir in _config_cache:
            return _config_cache[config_dir]
        else:
            config = _get_config(config_dir)
            _config_cache[config_dir] = config
            return config
