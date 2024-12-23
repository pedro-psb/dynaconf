from __future__ import annotations
from typing import Sequence


class TreePath(tuple):
    def as_str(self):
        return ".".join(self)

    def __add__(self, x: Sequence | str | int):
        if isinstance(x, list | tuple):
            return TreePath(tuple(self) + tuple(x))
        elif isinstance(x, str | int):
            return TreePath(tuple(self) + (x,))
        else:
            TypeError("Type not supported.")

    def __repr__(self):
        return f"{self.__class__.__name__}{super().__repr__()}"

    @staticmethod
    def ensure_path(path: TreePath | str) -> TreePath:
        def cast_int(s):
            try:
                return int(s)
            except ValueError:
                return s

        if isinstance(path, str):
            return TreePath([cast_int(val) for val in path.split(".")])
        return path

    @staticmethod
    def ensure_rooted(_data: dict):
        if "root" not in _data.keys():
            return {"root": _data}
        return _data


NodeKey = TreePath | str


class Tree:
    def __init__(self, instance_type: type):
        self.instance_type = instance_type
        self._data = {}

    def add(self, key: NodeKey, value):
        self._validate_value(value)
        if key in self._data:
            raise RuntimeError(f"Key {key!r} already exists.")
        self._data[key] = value

    def remove(self, key: NodeKey):
        self._data.pop(key)

    def swap(self, key_a: NodeKey, key_b: NodeKey):
        raise NotImplementedError()

    def _validate_value(self, value):
        if not isinstance(value, self.instance_type):
            raise TypeError(f"Node should have value type of {self.instance_type!r}")
