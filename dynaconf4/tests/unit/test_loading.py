from dynaconf.data_structs import LoadRequest
from dynaconf.dynaconf_options import SharedOptions
from dynaconf.loading import LoadingManager
import pytest


def test_basic_loading():
    opts = SharedOptions()
    lm = LoadingManager(opts)

    # without envs (DirectLoader default)
    data = {"foo": "from-load-1"}
    load_request = LoadRequest(
        loader_id="builtin.loaders.direct", uri="unit_test", data=data
    )
    lm.load_resource(load_request)

    # without envs
    data = {"default": {"foo": "from-load-2"}, "prod": {"foo": "prod-bar"}}
    load_request = LoadRequest(
        loader_id="builtin.loaders.direct",
        uri="unit_test",
        data=data,
        has_explicit_envs=True,
    )
    lm.load_resource(load_request)
    assert lm.get("default") == data["default"]
    assert lm.get("prod") == data["prod"]

    # loaded data stack
    load2 = lm.pop("default")
    load1 = lm.pop("default")
    assert load2["foo"] == "from-load-2"
    assert load1["foo"] == "from-load-1"

    msg = "consumed"
    with pytest.raises(ValueError, match=msg):
        lm.pop("default")

    # reset loaded stack
    lm.reset_loaded_stack("default")
    load2 = lm.pop("default")
    load1 = lm.pop("default")
    assert load2["foo"] == "from-load-2"
    assert load1["foo"] == "from-load-1"

    msg = "consumed"
    with pytest.raises(ValueError, match=msg):
        lm.pop("default")
