from _dynaconf.datastructures import LoadRequest, LoadContext, SchemaTree
from _dynaconf.coreutils import load
from _dynaconf.coreutils import LoaderRegistry
from dataclasses import dataclass
from unittest.mock import Mock

import pytest

def mock_schema_tree(path_types)->SchemaTree:
    """Mock a SchemaTree to return the types we want.
    
    Example:
        ```python
        >>> stree = mock_schema_tree(path_types=[(["mylist"], list), (["mydict, foo"], str)])
        >>> stree.get_key_type(["mylist"])
        list
        >>> stree.get_key_type(["mydict", "foo"])
        str
        >>> stree.get_key_type(["not_set"])
        None
        ```
    """
    stree = SchemaTree()
    def get_key_type(*key_path):
        return_type = None
        for item in path_types:
            item_path = item[0]
            item_type = item[1]
            for k in key_path:
                return_type = item_type
                break
        return return_type
    stree.get_key_type = get_key_type
    return stree


@dataclass
class Scenario:
    id: str
    load_request: LoadRequest
    expected: dict
    load_context: LoadContext = None
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
        envvar_data={"DYNACONF_MYKEY": "123"},
        expected={"default": {"mykey": "123"}},
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
        load_context=LoadContext(schema_tree=mock_schema_tree(path_types=[(("mylist",), list)]))
    ),
]


@pytest.mark.parametrize("scenario", scenarios)
def test_load(scenario: Scenario, monkeypatch):
    load_context = scenario.load_context or LoadContext(schema_tree=SchemaTree())  # type: ignore
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
