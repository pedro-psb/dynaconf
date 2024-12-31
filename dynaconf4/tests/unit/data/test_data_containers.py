from dynaconflib.datastructures import DataDict, DataList, SchemaTree
from dynaconflib.utils import container_items
from dynaconflib.exceptions import DynaconfNotInitialized
from dynaconflib.core import DynaconfCore

import pytest

data_set = [
    DataDict({"a": 1}),
    DataDict({"a": {"b": 1}}),
    DataDict({"a": {"b": {"c": 1}}}),
    DataList([1]),
    DataList([1, [2]]),
    DataList([1, [2, [3]]]),
    DataDict({"a": {"b": [1, {"c": 2}, 3]}}),
    DataList([1, [2, {"a": [3]}]]),
]


@pytest.mark.parametrize("data", data_set)
def test_data_containers(data):
    """All the ingested dict/list should be converted to DataDict/DataList."""

    def walk(container: dict | list):
        assert container.__class__ in (DataDict, DataList)
        for k, v in container_items(container):
            if isinstance(v, (dict, list)):
                walk(v)

    walk(data)


def test_core_initialized():
    data = DataDict()
    core = DynaconfCore("test", SchemaTree())

    with pytest.raises(DynaconfNotInitialized, match="not initialized"):
        data.__get_dynaconf__()

    data.__init_dynaconf__(core)
    assert core == data.__get_dynaconf__()
