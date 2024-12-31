from dynaconflib.datastructures import DataDict, DataList, SchemaTree
from dynaconflib.utils import container_items
from dynaconflib.exceptions import DynaconfNotInitialized
from dynaconflib.core import DynaconfCore

import pytest


def test_core_initialized():
    data = DataDict()
    core = DynaconfCore("test", SchemaTree())

    with pytest.raises(DynaconfNotInitialized, match="not initialized"):
        data.__get_dynaconf__()

    data.__init_dynaconf__(core)
    assert core == data.__get_dynaconf__()


data_set = (
    [
        {"a": 1},
        {"a": {"b": 1}},
        {"a": {"b": {"c": 1}}},
        [1],
        [1, [2]],
        [1, [2, [3]]],
        {"a": {"b": [1, {"c": 2}, 3]}},
        [1, [2, {"a": [3]}]],
    ],
)


@pytest.mark.parametrize("input", data_set)
def test_data_containers_init(input):
    """All the ingested dict/list via init should be converted to DataDict/DataList."""
    DataType = DataDict if isinstance(input, dict) else DataList
    data = DataType(input)

    def walk(container: dict | list):
        assert container.__class__ in (DataDict, DataList)
        for k, v in container_items(container):
            if isinstance(v, (dict, list)):
                walk(v)

    walk(data)


def test_dict_methods():
    d = DataDict()

    # Basic dict operations
    d["a"] = {"x": 1}
    assert isinstance(d["a"], DataDict)

    d.update({"b": [1, 2]})
    assert isinstance(d["b"], DataList)

    # Pop operations
    popped = d.pop("a")
    assert isinstance(popped, DataDict)

    # Clear and copy
    d_copy = d.copy()
    assert isinstance(d_copy, DataDict)
    d.clear()
    assert len(d) == 0


def test_list_methods():
    l = DataList()

    # Append
    l.append({"x": 1})
    assert isinstance(l[0], DataDict)

    # Extend
    l.extend([{"y": 2}, [1, 2]])
    assert isinstance(l[1], DataDict)
    assert isinstance(l[2], DataList)

    # Insert
    l.insert(0, {"z": 3})
    assert isinstance(l[0], DataDict)

    # Pop operations
    popped = l.pop()
    assert isinstance(popped, DataList)

    # Slice operations
    l[1:1] = [{"w": 4}]
    assert isinstance(l[1], DataDict)

    # Clear and copy
    d_copy = l.copy()
    assert isinstance(d_copy, DataList)
    l.clear()
    assert len(l) == 0


def test_nested_structures():
    d = DataDict({"a": [{"x": 1}, {"y": 2}], "b": {"c": [3, 4]}})

    assert isinstance(d["a"], DataList)
    assert isinstance(d["a"][0], DataDict)
    assert isinstance(d["b"], DataDict)
    assert isinstance(d["b"]["c"], DataList)


def test_method_preservation():
    d = DataDict()
    d["a"] = {"x": 1}

    # Dict methods
    assert list(d.keys()) == ["a"]
    assert list(d.values())[0]["x"] == 1
    assert list(d.items())[0][1]["x"] == 1

    l = DataList([1, {"x": 2}])
    # List methods
    assert l.count(1) == 1
    assert l.index({"x": 2}) == 1

    # Sort, reverse
    l = DataList([{"x": 2}, {"x": 1}])
    l.sort(key=lambda x: x["x"])
    assert l[0]["x"] == 1


def test_mutable_operations():
    d = DataDict()
    # Test setdefault
    item = d.setdefault("a", {"x": 1})
    assert isinstance(item, DataDict)

    # Test dict comprehension conversion
    d = DataDict({k: {"val": v} for k, v in [("a", 1), ("b", 2)]})
    assert all(isinstance(v, DataDict) for v in d.values())

    # Test list concatenation
    l = DataList()
    l += [{"x": 1}]
    assert isinstance(l[0], DataDict)

    # Test multiply
    l = DataList([{"x": 1}]) * 2
    assert isinstance(l[0], DataDict) and isinstance(l[1], DataDict)
