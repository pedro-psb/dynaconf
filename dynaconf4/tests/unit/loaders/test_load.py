from dynaconflib.datastructures import LoadRequest, LoadContext, SchemaTree, Index
from dataclasses import dataclass
import pytest
import os


@dataclass
class Scenario:
    id: str
    load_request: LoadRequest
    expected: dict
    file_data: dict = None
    envvar_data: dict = None
    schema_items: list[tuple] = None


direct = [
    Scenario(
        id="direct:no-root-envs",
        load_request=LoadRequest(
            loader_id="builtin.direct",
            uri="unit_test",
            direct_data={"foo": "from-load-1"},
        ),
        expected=[{"default": {"foo": "from-load-1"}}],
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
        expected=[{"default": {"foo": "from-load-2"}, "prod": {"foo": "prod-bar"}}],
    ),
]
envvars = [
    Scenario(
        id="envvar:no-nesting",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MY_KEY": "123"},
        schema_items=[(["my_key"], int)],
        expected=[{"default": {"my_key": "123"}}],
    ),
    Scenario(
        id="envvar:no-nesting-no-schema",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MY_KEY": "123"},
        schema_items=[(["my_key"], int)],
        expected=[{"default": {"my_key": "123"}}],
    ),
    Scenario(
        id="envvar:dict-nesting",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MYDICT__MYKEY": "123"},
        schema_items=[(["mydict"], dict), (["mydict", "mykey"], int)],
        expected=[{"default": {"mydict": {"mykey": "123"}}}],
    ),
    Scenario(
        id="envvar:dict-nesting2",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MYDICT__FOO__BAR__MYKEY": "123"},
        schema_items=[
            (["mydict"], dict),
            (["mydict", "foo"], dict),
            (["mydict", "foo", "bar"], dict),
            (["mydict", "foo", "bar", "mykey"], int),
        ],
        expected=[{"default": {"mydict": {"foo": {"bar": {"mykey": "123"}}}}}],
    ),
    Scenario(
        id="envvar:list-nesting",
        load_request=LoadRequest(
            loader_id="builtin.environ",
            uri="unit_test",
        ),
        envvar_data={"DYNACONF_MYLIST__0": "123"},
        schema_items=[
            (["mylist"], list),
            (["mylist", Index()], int),
        ],
        expected=[{"default": {"mylist": ["123"]}}],
        # load_context=LoadContext(schema_tree=mock_schema_tree(path_types=[(("mylist",), list)]))
    ),
]

expected_file_data = {
    "no-namespaces": {
        "default": {
            "database": {"host": "https://localhost", "port": 5432},
            "user": {"name": "john"},
        }
    },
    "with-namespaces": {
        "default": {
            "database": {"host": "https://default", "port": 1234},
        },
        "main": {
            "database": {"host": "https://localhost", "port": 5432},
        },
    },
}

files = [
    Scenario(
        id="files:toml:no-namespace",
        load_request=LoadRequest(
            loader_id="builtin.toml",
            uri=f"{os.getcwd()}/tests/unit/loaders/data/no-namespaces.toml",
        ),
        expected=[expected_file_data["no-namespaces"]],
    ),
    Scenario(
        id="files:toml:with-namespace",
        load_request=LoadRequest(
            loader_id="builtin.toml",
            uri=f"{os.getcwd()}/tests/unit/loaders/data/with-namespaces.toml",
            namespace_in_root=True,
        ),
        expected=[expected_file_data["with-namespaces"]],
    ),
    Scenario(
        id="files:toml:no-namespaces",
        load_request=LoadRequest(
            loader_id="builtin.json",
            uri=f"{os.getcwd()}/tests/unit/loaders/data/no-namespaces.json",
        ),
        expected=[expected_file_data["no-namespaces"]],
    ),
    Scenario(
        id="files:toml:with-namespaces",
        load_request=LoadRequest(
            loader_id="builtin.json",
            uri=f"{os.getcwd()}/tests/unit/loaders/data/with-namespaces.json",
            namespace_in_root=True,
        ),
        expected=[expected_file_data["with-namespaces"]],
    ),
]
scenarios = direct + envvars + files


def get_ids(scenarios):
    return [f"LOAD-{i:02}:{x.id}" for i, x in enumerate(scenarios)]


@pytest.mark.parametrize("scenario", scenarios, ids=get_ids(scenarios))
def test_load(scenario: Scenario, monkeypatch, registries):
    load_registry = registries.loaders
    # setup schema
    schema = SchemaTree(strict=True)
    schema_items = scenario.schema_items or []
    for path, t in schema_items:
        schema.add(path, t)
    load_context = LoadContext(schema_tree=schema)

    with monkeypatch.context() as m:
        # mock environ
        envvar_data = scenario.envvar_data or {}
        for k, t in envvar_data.items():
            m.setenv(k, t)
        # test
        load_request = scenario.load_request
        loader = load_registry.get(load_request.loader_id)
        result = loader.load(load_request, load_context)
        assert result.data == scenario.expected
