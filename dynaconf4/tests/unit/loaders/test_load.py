from dynaconflib.datastructures import LoadRequest, LoadContext, SchemaTree
from dynaconflib.builtin import setup_loaders
from dynaconflib.registry import LoaderRegistry
from dataclasses import dataclass
import pytest

load_registry = LoaderRegistry("load_test")
setup_loaders(load_registry)


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
            namespace_in_root=True,
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
    Scenario(
        id="envvar:dict-nesting",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MYDICT__MYKEY": "123"},
        expected={"default": {"mydict": {"mykey": "123"}}},
    ),
    Scenario(
        id="envvar:dict-nesting2",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MYDICT__FOO__BAR__MYKEY": "123"},
        expected={"default": {"mydict": {"foo": {"bar": {"mykey": "123"}}}}},
    ),
    Scenario(
        id="envvar:list-nesting",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MYLIST__0": "123"},
        expected={"default": {"mylist": ["@insert 0 123"]}},
        # load_context=LoadContext(schema_tree=mock_schema_tree(path_types=[(("mylist",), list)]))
    ),
]


@pytest.mark.parametrize("scenario", scenarios)
def test_load(scenario: Scenario, monkeypatch):
    load_context = LoadContext(schema_tree=SchemaTree())  # type: ignore
    with monkeypatch.context() as m:
        # mock environ
        if scenario.envvar_data:
            for k, v in scenario.envvar_data.items():
                m.setenv(k, v)
        # test
        result = scenario.load_request.load(load_registry, load_context)
        for env, data in scenario.expected.items():
            assert result[env] == data
