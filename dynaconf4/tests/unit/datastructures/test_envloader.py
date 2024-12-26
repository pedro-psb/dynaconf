from dynaconflib.builtin.loaders import EnvLoader
from typing import NamedTuple


Empty = object()


class SchemaNode(NamedTuple):
    key: str | int
    key_type: type
    value_type: type
    children_key_type: type

    def __eq__(self, o):
        return all([getattr(o, f) == getattr(self, f) for f in self._fields])


class Index(NamedTuple):
    value: int = 0

    def __eq__(self, o):
        return type(self) is type(o)

    def __hash__(self):
        return hash(Index)


class Schema:
    def __init__(self):
        self.type_map = {}
        self.root = SchemaNode("root", str, dict, str)

    def add(self, key_path, value_type, children_key_type=str):
        # TODO make sanity checks.
        # E.g:
        # 1. [(A, k=str, v=list), (B, k=str, v=int)] is invalid, because
        #    Node A is a list and its child B has k=str (must be INDEX)
        # 2. [(A, v=int), (B, v=bool)] is invalid, because Node A has
        #    children, but it is has value=int
        key = key_path[-1]
        key_type = int if isinstance(key, Index) else type(key)
        if value_type not in (dict, list):
            children_key_type = None
        elif value_type is list:
            children_key_type = int
        self.type_map[tuple(key_path)] = SchemaNode(
            key, key_type, value_type, children_key_type
        )

    def get(self, key_path) -> SchemaNode:
        return self.type_map[tuple(key_path)]

    def raw_to_schema_path(self, raw_path: list[str]) -> list[SchemaNode]:
        final = []
        parent_node = self.root
        for i in range(len(raw_path)):
            # take each sub patch from start to i
            cur_path = raw_path[: i + 1]
            key = cur_path[-1]
            # handle case where parent is list
            if parent_node.value_type is list:
                key = Index(int(key))
                cur_path = cur_path[:i] + [key]
                raw_path = cur_path + raw_path[i + 1 :]
            # add to transformed list
            current_node = self.get(tuple(cur_path))._replace(key=key)
            final.append(current_node)
            # update
            parent_node = current_node
        return final

    def __str__(self):
        return str(self.type_map)


def is_last(it, i):
    return i == len(it) - 1


def pad_with_empty(list_container, i): ...


def schema_path_to_data(schema_path: list[SchemaNode], value) -> dict:
    """
    Transform a path in the form (schema_path: value) to its expanded pyhton data.

    Example:
        path_to_data(["a", "b", "c"], value) -> {"a": {"b": {"c": value}}}
    """
    terminal_value = value
    parent_v = {}
    final_data = parent_v

    for i, current_schema in enumerate(schema_path):
        current_type = current_schema.value_type
        current_k = current_schema.key
        current_v = current_type() if not is_last(schema_path, i) else terminal_value
        # fill parent_v to sufficient length if a list
        if isinstance(parent_v, list):
            current_k = current_k.value
            for i in range(current_k + 1):
                parent_v.append(Empty)
            # breakpoint()
        # add to parent (works for dict and lists)
        parent_v[current_k] = current_v
        # update
        parent_v = current_v
    return final_data


def raw_path_to_data(raw_path: list[str], value, schema: Schema) -> dict:
    schema_path = schema.raw_to_schema_path(raw_path)
    # breakpoint()
    return schema_path_to_data(schema_path, value)


def test_schema_get_path():
    schema = Schema()
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
    schema = Schema()
    schema.add(["a"], dict)
    schema.add(["a", "b"], dict)
    schema.add(["a", "b", "c"], int)

    raw_path = ["a", "b", "c"]
    result = raw_path_to_data(raw_path, value=123, schema=schema)

    expected = {"a": {"b": {"c": 123}}}
    assert result == expected


def test_envloader_list():
    schema = Schema()
    schema.add(["a"], list)
    schema.add(["a", Index()], dict)
    schema.add(["a", Index(), "b"], int)

    raw_path = ["a", "0", "b"]
    result = raw_path_to_data(raw_path, value=123, schema=schema)

    expected = {"a": [{"b": 123}]}
    assert result == expected


def test_envloader_list2():
    schema = Schema()
    schema.add(["a"], list)
    schema.add(["a", Index()], dict)
    schema.add(["a", Index(), "b"], int)

    raw_path = ["a", "3", "b"]
    result = raw_path_to_data(raw_path, value=123, schema=schema)

    expected = {"a": [Empty, Empty, Empty, {"b": 123}]}
    assert result == expected
