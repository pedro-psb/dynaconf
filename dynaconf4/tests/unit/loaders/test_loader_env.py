from dynaconflib.builtin.loaders import EnvLoader
from dynaconflib.datastructures import SchemaTree, SchemaNode, Index
from dynaconflib.utils import Empty


def test_schema_get_path():
    schema = SchemaTree()
    schema.add(["a"], list)
    schema.add(["a", Index()], dict)
    schema.add(["a", Index(), "b"], dict)
    schema.add(["a", Index(), "b", "0"], int)
    path = ["a", "1", "b", "0"]

    expected = [
        SchemaNode("a", str, list, int),
        SchemaNode(Index(1), int, dict, str),
        SchemaNode("b", str, dict, str),
        SchemaNode("0", str, int, None),
    ]
    result = schema.raw_to_schema_path(path)
    assert result == expected
    assert result[1].key.value == expected[1].key.value


def test_envloader_simple():
    schema = SchemaTree()
    schema.add(["a"], dict)
    schema.add(["a", "b"], dict)
    schema.add(["a", "b", "c"], int)

    raw_path = ["a", "b", "c"]
    result = EnvLoader.path_to_data(raw_path, value=123, schema=schema)

    expected = {"a": {"b": {"c": 123}}}
    assert result == expected


def test_envloader_list():
    schema = SchemaTree()
    schema.add(["a"], list)
    schema.add(["a", Index()], dict)
    schema.add(["a", Index(), "b"], int)

    raw_path = ["a", "0", "b"]
    result = EnvLoader.path_to_data(raw_path, value=123, schema=schema)

    expected = {"a": [{"b": 123}]}
    assert result == expected


def test_envloader_list2():
    schema = SchemaTree()
    schema.add(["a"], list)
    schema.add(["a", Index()], dict)
    schema.add(["a", Index(), "b"], int)

    raw_path = ["a", "3", "b"]
    result = EnvLoader.path_to_data(raw_path, value=123, schema=schema)

    expected = {"a": [Empty, Empty, Empty, {"b": 123}]}
    assert result == expected
