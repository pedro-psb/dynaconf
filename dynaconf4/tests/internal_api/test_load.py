from _dynaconf.datastructures import LoadRequest
from _dynaconf.load import load


def test_load_with_no_root_level_envs():
    data = {"foo": "from-load-1"}
    load_request = LoadRequest(
        loader_id="builtin.loaders.direct", uri="unit_test", direct_data=data
    )
    result = load(load_request)
    assert result["default"] == data


def test_load_with_root_level_envs():
    data = {"default": {"foo": "from-load-2"}, "prod": {"foo": "prod-bar"}}
    load_request = LoadRequest(
        loader_id="builtin.loaders.direct",
        uri="unit_test",
        direct_data=data,
        has_explicit_envs=True,
    )
    result = load(load_request)
    assert result["default"] == data["default"]
    assert result["prod"] == data["prod"]
