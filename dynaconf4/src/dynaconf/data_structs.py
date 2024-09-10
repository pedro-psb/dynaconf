from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import rich

if TYPE_CHECKING:
    from .dynaconf_options import SharedOptions


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


@dataclass
class LoaderSpec:
    loader_id: str
    uri: str
