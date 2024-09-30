from _dynaconf.datastructures import LoadRequest
from _dynaconf.load import load
from _dynaconf.load_registry import LoaderRegistry


def test_load_with_no_root_level_envs():
    load_registry = LoaderRegistry()
    data = {"foo": "from-load-1"}
    load_request = LoadRequest(
        loader_id="builtin.direct", uri="unit_test", direct_data=data
    )
    result = load(load_request, load_registry)
    assert result["default"] == data


def test_load_with_root_level_envs():
    load_registry = LoaderRegistry()
    data = {"default": {"foo": "from-load-2"}, "prod": {"foo": "prod-bar"}}
    load_request = LoadRequest(
        loader_id="builtin.direct",
        uri="unit_test",
        direct_data=data,
        has_explicit_envs=True,
    )
    result = load(load_request, load_registry)
    assert result["default"] == data["default"]
    assert result["prod"] == data["prod"]
