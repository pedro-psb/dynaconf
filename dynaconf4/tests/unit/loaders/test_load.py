from dynaconflib.datastructures import LoadRequest, LoadContext, SchemaTree, Index
from dataclasses import dataclass
import pytest


@dataclass
class Scenario:
    id: str
    load_request: LoadRequest
    expected: dict
    file_data: dict = None
    envvar_data: dict = None
    schema_items: list[tuple] = None


scenarios = [
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


@pytest.mark.parametrize("scenario", scenarios)
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
