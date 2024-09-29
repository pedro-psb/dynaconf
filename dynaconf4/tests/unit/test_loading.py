import pytest

from dynaconf.data_structs import LoadRequest
from dynaconf.dynaconf_options import SharedOptions
from dynaconf.loading import LoadingManager
import os


@pytest.fixture
def default_lm():
    opts = SharedOptions()
    lm = LoadingManager(opts)
    return lm


def test_load_with_no_root_level_envs(default_lm: LoadingManager):
    data = {"foo": "from-load-1"}
    load_request = LoadRequest(
        loader_id="builtin.loaders.direct", uri="unit_test", direct_data=data
    )
    result = default_lm.load_resource(load_request)
    assert result["default"] == data


def test_load_with_root_level_envs(default_lm: LoadingManager):
    data = {"default": {"foo": "from-load-2"}, "prod": {"foo": "prod-bar"}}
    load_request = LoadRequest(
        loader_id="builtin.loaders.direct",
        uri="unit_test",
        direct_data=data,
        has_explicit_envs=True,
    )
    result = default_lm.load_resource(load_request)
    assert result["default"] == data["default"]
    assert result["prod"] == data["prod"]
