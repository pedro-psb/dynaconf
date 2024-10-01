from _dynaconf.datastructures import LoadRequest, LoadContext
from _dynaconf.load import load
from _dynaconf.load_registry import LoaderRegistry
from dataclasses import dataclass
import pytest


@dataclass
class Scenario:
    id: str
    data: dict
    load_request: LoadRequest
    expected: dict


scenarios = [
    Scenario(
        id="direct:no-root-envs",
        data=None,
        load_request=LoadRequest(
            loader_id="builtin.direct",
            uri="unit_test",
            direct_data={"foo": "from-load-1"},
        ),
        expected={"default": {"foo": "from-load-1"}},
    ),
    Scenario(
        id="direct:with-root-envs",
        data=None,
        load_request=LoadRequest(
            loader_id="builtin.direct",
            uri="unit_test",
            direct_data={
                "default": {"foo": "from-load-2"},
                "prod": {"foo": "prod-bar"},
            },
            has_explicit_envs=True,
        ),
        expected={"default": {"foo": "from-load-2"}, "prod": {"foo": "prod-bar"}},
    ),
]


@pytest.mark.parametrize("scenario", scenarios)
def test_load(scenario: Scenario):
    load_context = LoadContext()  # type: ignore
    load_registry = LoaderRegistry()
    result = load(scenario.load_request, load_registry, load_context)
    for env, data in scenario.expected.items():
        assert result[env] == data

