import json
from pathlib import Path

import yaml
from pyfakefs.fake_filesystem import FakeFilesystem

from appcfg.appcfg import get_config

CONFIG_DIR = Path(__file__).parent / "config"


def test_default(fs: FakeFilesystem, monkeypatch):
    fs.create_file(CONFIG_DIR / "default.yml", contents="key: value")
    assert {"key": "value"} == get_config(__name__, cached=False)

    monkeypatch.setenv("ENV", "test")
    assert {"key": "value"} == get_config(__name__, cached=False)


def test_override(fs: FakeFilesystem, monkeypatch):
    fs.create_file(CONFIG_DIR / "default.yml", contents="source: default")
    fs.create_file(CONFIG_DIR / "development.json", contents='{"source": "dev"}')
    fs.create_file(CONFIG_DIR / "production.yml", contents="source: production")

    def assert_source(source: str):
        assert {"source": source} == get_config(__name__, cached=False)

    assert_source("default")
    monkeypatch.setenv("ENV", "default")
    assert_source("default")

    monkeypatch.setenv("ENV", "development")
    assert_source("dev")

    monkeypatch.delenv("ENV")
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert_source("production")


def test_merging(fs: FakeFilesystem, monkeypatch):
    fs.create_file(
        CONFIG_DIR / "default.yaml",
        contents=yaml.dump({"a": 1, "b": {"c": 1, "d": 1}}),
    )
    fs.create_file(
        CONFIG_DIR / "test.json", contents=json.dumps({"a": "a", "b": {"c": 2}}),
    )

    monkeypatch.setenv("ENV", "test")
    assert {"a": "a", "b": {"c": 2, "d": 1}} == get_config(__name__, cached=False)


def test_env_var_override(fs: FakeFilesystem, monkeypatch):
    fs.create_file(
        CONFIG_DIR / "default.yaml",
        contents=yaml.dump({"a": "orig", "b": {"c": "orig", "d": "orig"}}),
    )
    fs.create_file(
        CONFIG_DIR / "env-vars.yaml",
        contents=yaml.dump({"a": "A", "b": {"c": "C", "d": "D"}}),
    )

    monkeypatch.setenv("A", "env")
    monkeypatch.setenv("C", "env")
    assert {"a": "env", "b": {"c": "env", "d": "orig"}} == get_config(
        __name__, cached=False
    )


def test_caching(fs: FakeFilesystem):
    config_file = Path(CONFIG_DIR) / "default.yml"

    fs.create_file(config_file, contents="version: 1")

    config = get_config(__name__)

    assert {"version": 1} == config
    assert get_config(__name__) is config

    with config_file.open("w") as f:
        f.write("version: 2")

    assert get_config(__name__) is config

    new_config = get_config(__name__, cached=False)
    assert new_config is not config
    assert {"version": 2} == new_config
