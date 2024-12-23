from typing import Callable
from functools import partial


class Registry:
    ids = set()

    def __init__(self, id: str, instance_cls: type):
        if id in Registry.ids:
            raise KeyError("Id already exists")
        Registry.ids.add(id)

        self.id = id
        self.data = {}
        self.instance_cls = instance_cls

    def get(self, key: str):
        return self.data[key]

    def add(self, key: str, value):
        if key in self.data:
            raise KeyError("Key already exist:", key)
        self._validate_value(value)
        self.data[key] = value

    def _validate_value(self, value):
        if not isinstance(value, self.instance_cls):
            raise TypeError(f"Value must be of type {self.instance_cls!r}")


def test_regsitry():
    import pytest

    # given
    IntRegistry = partial(Registry, instance_cls=int)
    BoolRegistry = partial(Registry, instance_cls=bool)

    int_reg = IntRegistry("foo")
    bool_reg = BoolRegistry("bar")

    # assert happy add/get
    int_reg.add("foo", 123)
    int_reg.add("bar", 456)
    assert int_reg.get("foo") == 123
    assert int_reg.get("bar") == 456
    bool_reg.add("foo", True)
    assert bool_reg.get("foo") is True

    # assert cant use wrong type
    with pytest.raises(TypeError):
        int_reg.add("new", "foo")

    # assert cant have duplicate key
    with pytest.raises(KeyError):
        int_reg.add("foo", 789)

    # assert cant have duplicate registry name
    with pytest.raises(KeyError):
        IntRegistry("foo")
