from _dynaconf.datastructures import LoadRequest, LoadContext, SchemaTree
from _dynaconf.coreutils import load
from _dynaconf.coreutils import LoaderRegistry
from dataclasses import dataclass
import pytest


@dataclass
class Scenario:
    id: str
    load_request: LoadRequest
    expected: dict
    file_data: dict = None
    envvar_data: dict = None


scenarios = [
    Scenario(
        id="direct:no-root-envs",
        load_request=LoadRequest(
            loader_id="builtin.direct",
            uri="unit_test",
            direct_data={"foo": "from-load-1"},
        ),
        expected={"default": {"foo": "from-load-1"}},
    ),
    Scenario(
        id="direct:with-root-envs",
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
    Scenario(
        id="envvar:no-nesting",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MY_KEY": "123"},
        expected={"default": {"my_key": "123"}},
    ),
]


@pytest.mark.parametrize("scenario", scenarios)
def test_load(scenario: Scenario, monkeypatch):
    load_context = LoadContext(schema_tree=SchemaTree())  # type: ignore
    load_registry = LoaderRegistry()
    with monkeypatch.context() as m:
        # mock environ
        if scenario.envvar_data:
            for k, v in scenario.envvar_data.items():
                m.setenv(k, v)
        # test
        result = load(scenario.load_request, load_registry, load_context)
        for env, data in scenario.expected.items():
            assert result[env] == data
