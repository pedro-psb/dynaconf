from dynaconflib.public import FileLoader
from dynaconflib.datastructures import LoadRequest
from pathlib import Path
import os


def test_load_factory():
    loader = FileLoader("*toml")
    result = loader.build()
    expected_file = str(Path("pyproject.toml").absolute())
    assert isinstance(result, list)
    assert result[0] == LoadRequest("builtin.toml", expected_file)
