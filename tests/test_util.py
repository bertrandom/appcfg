import sys
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_voluptuous import S
from voluptuous import Contains, Unordered

from appcfg.exceptions import (
    ConfigFileNotFoundError,
    InvalidModuleNameError,
    YamlExtraRequiredError,
)
from appcfg.util import (
    compile_env_vars_template,
    get_config_dir,
    get_environment,
    get_module_path,
    get_root_path,
    load_config_file,
    merge_configs,
    validate_env_vars_template,
)

THIS_FILE = Path(__file__)


def test_get_module_path():
    assert THIS_FILE == get_module_path(__name__)
    assert THIS_FILE.parents[1] / "appcfg/__init__.py" == get_module_path("appcfg")

    with pytest.raises(InvalidModuleNameError, match="my_invalid_module_name"):
        get_module_path("my_invalid_module_name")


def test_get_root_path():
    ROOT = Path("/home/user/project")

    # Standalone module
    assert ROOT == get_root_path(ROOT / "mymodule.py", "mymodule")

    # Script
    assert ROOT == get_root_path(ROOT / "myscript.py", "__main__")

    # Package
    assert ROOT / "mypackage" == get_root_path(
        ROOT / "mypackage/__init__.py", "mypackage"
    )

    # Module in a package
    assert ROOT / "mypackage" == get_root_path(
        ROOT / "mypackage/module.py", "mypackage.module"
    )

    # Package in a package
    assert ROOT / "mypackage" == get_root_path(
        ROOT / "mypackage/subpackage/__init__.py", "mypackage.subpackage"
    )

    # Module in a sub package
    assert ROOT / "mypackage" == get_root_path(
        ROOT / "mypackage/subpackage/module.py", "mypackage.subpackage.module"
    )


def test_get_config_dir(fs):
    # THIS_FILE.parent is a PurePath and would fail assertions, hence the `Path(...)`
    TEST_CONFIG_DIR = Path(THIS_FILE.parent) / "config"

    with pytest.raises(FileNotFoundError):
        get_config_dir(__name__)

    fs.create_dir(TEST_CONFIG_DIR)
    assert TEST_CONFIG_DIR == get_config_dir(__name__)


@pytest.mark.parametrize(
    "fakefile",
    [("json", '{ "type": "json" }'), ("yml", "type: yml"), ("yaml", "type: yaml")],
)
@pytest.mark.parametrize("strict", [False, True])
def test_load_config_file(fakefile, strict, fs: FakeFilesystem):
    suffix, contents = fakefile
    path = Path("/path/to")

    if strict:
        with pytest.raises(ConfigFileNotFoundError, match="file.{json,yml,yaml}"):
            load_config_file(path, "file", strict=strict)
    else:
        assert load_config_file(path, "file", strict=strict) is None

    fs.create_file(path / ("file." + suffix), contents=contents)

    assert {"type": suffix} == load_config_file(path, "file", strict=strict)


@pytest.mark.parametrize("suffix", ["yml", "yaml"])
def test_load_config_file_yaml_without_pyyaml(suffix, fs, monkeypatch):
    monkeypatch.setitem(sys.modules, "yaml", None)
    path = Path("/path/to")
    fs.create_file(path / ("file." + suffix))

    with pytest.raises(YamlExtraRequiredError):
        load_config_file(path, "file")


@pytest.mark.parametrize(
    "condition",
    [
        ("", "default"),
        ("dev", "development"),
        ("develop", "development"),
        ("anythingelse", "anythingelse"),
    ],
)
@pytest.mark.parametrize("name", ["ENV", "PY_ENV", "ENVIRONMENT"])
def test_get_environment(condition, name, monkeypatch):
    value, expected_result = condition
    monkeypatch.setenv(name, value)
    assert expected_result == get_environment()


def test_merge_configs():
    # Test flat overriding
    assert {"a": "old", "b": "new", "c": 2, "d": [2], "e": True} == merge_configs(
        base={"a": "old", "b": "old", "c": 1, "d": [1], "e": 42},
        override={"b": "new", "c": 2, "d": [2], "e": True},
    )

    # Test nested overriding
    assert {
        "a": {"a": "old", "b": 2, "c": False, "d": "new"},
        "b": "old",
    } == merge_configs(
        base={"a": {"a": "old", "b": 1, "c": "old"}, "b": "old"},
        override={"a": {"b": 2, "c": False, "d": "new"}},
    )


def test_validate_env_vars_template():
    def get_warning_messages(record):
        return [str(w.message) for w in record.list]

    # Test space warnings
    template = {
        "a": "VALID",
        "b": "IN VALID",
        "c": {"d": "IN VALID", "e": {"f": "IN VALID"}},
    }

    with pytest.warns(UserWarning, match="Ignoring") as record:
        validate_env_vars_template(template)

    assert S(
        Unordered([Contains(" b"), Contains(" c.d"), Contains(" c.e.f")])
    ) == get_warning_messages(record)
    assert {"a": "VALID", "c": {"e": {}}} == template

    # Test non-string warnings
    template = {
        "a": "VALID",
        "b": 1,
        "c": {"d": [], "e": {"f": True}},
    }

    with pytest.warns(UserWarning, match="Ignoring") as record:
        validate_env_vars_template(template)

    assert S(
        Unordered([Contains(" b"), Contains(" c.d"), Contains(" c.e.f")])
    ) == get_warning_messages(record)
    assert {"a": "VALID", "c": {"e": {}}} == template


def test_compile_env_vars_template(monkeypatch):
    template = {"a": "A", "b": {}, "c": {"d": "D", "e": {}}}
    compile_env_vars_template(template)
    assert {} == template

    template = {"a": "A", "b": {}, "c": {"d": "D", "e": {}}}
    monkeypatch.setenv("A", "a")
    monkeypatch.setenv("D", "d")
    compile_env_vars_template(template)
    assert {"a": "a", "c": {"d": "d"}} == template
