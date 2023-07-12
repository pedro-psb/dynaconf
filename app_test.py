import os
from pprint import pprint
from textwrap import dedent
from unittest import mock

import pytest
from dynaconf import Dynaconf, inspect_settings
from dynaconf.utils.inspect import get_history


def create_file(filename: str, data: str) -> str:
    """Utility to help create files"""
    with open(filename, "w") as file:
        file.write(dedent(data))
    return filename


def mock_environ(environ: dict):
    return mock.patch.dict(os.environ, environ)


def test_trivial(tmp_path):
    file_a = create_file(
        tmp_path / "a.toml",
        """
        foo="from_a"
        dicty={x=1, y=2, z=3}
        listy=['a','b','c']
        """,
    )
    environ = {
        "DYNACONF_DICTY__X": "by_env",
        "DYNACONF_LISTY": "@merge by_env",
    }
    with mock_environ(environ):
        settings = Dynaconf(settings_file=file_a)
        assert settings.dicty.x == "by_env"
        assert settings.listy[0] == "a"
        assert settings.listy[-1] == "by_env"


        inspect_settings(settings)
        # history = get_history(settings)
        # print()
        # pprint(history)
        # pprint(settings._loaded_by_loaders)
