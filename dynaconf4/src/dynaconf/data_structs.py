from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import rich


class BaseOptions:
    def print(self):
        rich.print(self)


class DataDict(dict): ...


class DataList(list): ...


class MergeOperation:
    def __init__(self, key: str):
        self.key = key

    def run(self, key_container: dict | list) -> None:
        """Run the operation.

        Implementation should mutate the key's container.
        """


class LazyValue:
    def __init__(self, key: str):
        self.key = key

    def evaluate(self): ...


class MergeTree:
    def __init__(self, data: DataDict, merge_operations: list[MergeOperation]):
        self.data = data
        self.merge_operations = merge_operations

    @classmethod
    def from_raw_data(cls, raw_data: dict, schema_tree: SchemaTree):
        data_dict = DataDict()
        merge_operations = [MergeOperation("key")]
        return MergeTree(data_dict, merge_operations)


class LazyTree:
    data: DataDict
    lazy_values: list[LazyValue]


@dataclass
class SchemaTree: ...


class LoaderSpec(NamedTuple):
    loader_id: str
    uri: str
    order: int


class LoadedDataStack:
    def __init__(self):
        self.stack = []
        self.index = 0

    def add(self, loaded_data: LoadedData):
        """Add item to stack."""
        self.stack.append(loaded_data)
        self.index += 1

    def pop(self) -> DataDict:
        """Virtually pops from the top of the stack.

        The loaded data is not removed from storate.
        """
        if not self.stack:
            raise ValueError("The stack is empty.")

        if self.index == 0:
            raise ValueError("All stack items were consumed.")
        return self.stack.pop()

    def reset_index(self):
        self.index = len(self.stack) - 1
