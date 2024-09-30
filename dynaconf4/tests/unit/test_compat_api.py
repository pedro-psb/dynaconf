import pytest

from dynaconf.user_api import CompatDynaconf as Dynaconf
import os


@pytest.fixture
def mockenv(monkeypatch):
    """Foo bar."""

    class Mockenv:
        def __init__(self, env: dict) -> None:
            for k, v in env.items():
                monkeypatch.setenv(k, v)

        def __enter__(self): ...

        def __exit__(self, *unused):
            monkeypatch.undo()

    return Mockenv


def test_mockenv(mockenv):
    env = {"foo": "bar"}

    assert "foo" not in os.environ
    with mockenv(env):
        assert "foo" in os.environ
    assert "foo" not in os.environ


def patch_env(m, env):
    for k, v in env.items():
        m.setenv(k, v)


def test_from_file():
    settings = Dynaconf(settings_file=["settings.toml"])
    assert settings


def test_from_os_environ(monkeypatch):
    env = {
        "DYNACONF_FOO": "bar",
        "DYNACONF_spam": "eggs",
        "DYNACONF_DICTY__KEY_A": "123",
        "DYNACONF_DICTY__KEY_B": "456",
        "DYNACONF_LISTY": "@json [1,2,3,4]",
    }
    with monkeypatch.context() as m:
        patch_env(m, env)
        settings = Dynaconf()
        assert settings
