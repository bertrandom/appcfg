import warnings
from importlib.util import find_spec
from os import environ
from pathlib import Path

from deepmerge import Merger

from appcfg.exceptions import (
    ConfigFileNotFoundError,
    InvalidModuleNameError,
    YamlExtraRequiredError,
)


def get_module_path(module_name: str) -> Path:
    """
    Given a module's name, returns the path of the source file associated with it
    """
    spec = find_spec(module_name)
    if spec is None:
        raise InvalidModuleNameError(module_name=module_name)
    return Path(spec.origin)


def get_root_path(module_path: Path, module_name: str) -> Path:
    """
    Given a module's path and name, returns the root directory of the project the module
    belongs to
    """
    depth = len(module_name.split(".")) - 1

    if depth == 0 or module_path.name == "__init__.py":
        # module_name refers to a standalone module / script (depth=0), or a package
        return module_path.parents[depth]

    # module_name refers to a module in a package
    return module_path.parents[depth - 1]


def get_config_dir(module_name) -> Path:
    """
    Given a module's name, returns the path of the corresponding config directory or
    raises a `FileNotFoundError` if the directory does not exist.
    """
    path = get_root_path(get_module_path(module_name), module_name) / "config"
    return path.resolve(strict=True)


def load_config_file(config_dir: Path, name: str, strict=False):
    """
    Parses a json or yaml file with the base name `name` from `config_dir`, if a
    corresponding config file exists there. Otherwise, `None` is returned if `strict` is
    `False`, and a `FileNotFoundError` is raised if `strict` is `True`.
    """
    base_path = config_dir / name

    for suffix in ["json", "yml", "yaml"]:
        path = base_path.with_suffix("." + suffix)
        if path.is_file():
            with path.open() as f:
                if suffix == "json":
                    import json

                    return json.load(f)
                else:
                    try:
                        import yaml
                    except ModuleNotFoundError:
                        raise YamlExtraRequiredError()

                    return yaml.safe_load(f)

    if strict:
        raise ConfigFileNotFoundError(base_path.as_posix() + ".{json,yml,yaml}")


def get_environment():
    """
    If an `ENV`, `PY_ENV`, or `ENVIRONMENT` environment variable is set, return the
    value of it. Otherwise, return "default".

    Special cases:
        * "dev" and "develop" are mapped to "development"
    """
    value = None
    for key in ["ENV", "PY_ENV", "ENVIRONMENT"]:
        if key in environ:
            value = environ[key]
            break
    if value is None or value == "":
        return "default"

    if value in {"dev", "develop"}:
        return "development"

    return value


def merge_configs(base: dict, override: dict):
    """
    Recursively merge `override` into `base`.
    """
    return Merger(
        [(list, ["override"]), (dict, ["merge"])], ["override"], ["override"],
    ).merge(base, override)


def validate_env_vars_template(template: dict):
    """
    Recursively check if the given dict contains only non-space-containing string
    values. If any other value is found, a warning is issued and the corresponding key
    is removed.
    """

    def validate(tpl: dict, path: str = ""):
        if path != "":
            path += "."
        for key, value in list(tpl.items()):
            key_path = path + key
            if isinstance(value, dict):
                validate(value, key_path)
                continue

            if not isinstance(value, str):
                warnings.warn(
                    (
                        "The env-vars config file contains a value of type {type} at {key}. "
                        "Only string values can be used to specify environment variables. "
                        "Ignoring {key}."
                    ).format(type=type(value), key=key_path)
                )
                tpl.pop(key)
                continue

            if " " in value:
                warnings.warn(
                    (
                        "Environment variables may not contain spaces. "
                        'Ignoring "{value}" at {key} in env-vars config file.'
                    ).format(value=value, key=key_path)
                )
                tpl.pop(key)
                continue

    validate(template)


def compile_env_vars_template(template: dict):
    """
    Given a (possibly recursive) dict that contains environment variable names, replace
    each name by the corresponding environmen variable's value, if set, or pop the key
    from the dict otherwise. Finally, recursively prune empty values from the dict.
    """

    def compile(tpl: dict):
        for key, value in list(tpl.items()):
            if isinstance(value, dict):
                compile(value)
                continue

            # values has to be a string at this point
            if value in environ:
                tpl[key] = environ[value]
            else:
                tpl.pop(key)

    compile(template)

    def prune(tpl: dict):
        """
        Recursively remove empty dicts and None values from a dict.
        """
        for key, value in list(tpl.items()):
            if isinstance(value, dict):
                if len(value) > 0:
                    prune(value)
                if len(value) == 0:
                    tpl.pop(key)

    prune(template)
