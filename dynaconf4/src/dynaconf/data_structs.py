from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, NamedTuple, Optional, TypeVar

import rich


class BaseOptions:
    def print(self):
        rich.print(self)


class DataDict(dict):
    def __init__(self, *args, **kwargs):
        self.__dynaconf_data__ = {}
        super().__init__(*args, **kwargs)

    def __init_dynaconf__(self, dynaconf_api):
        self.__dynaconf_data__["dynaconf_api"] = dynaconf_api

    def get_dynaconf(self):
        dynaconf_api = self.__dynaconf_data__.get("dynaconf_api", None)
        if not dynaconf_api:
            raise RuntimeError("Dynaconf not initialized.")
        return dynaconf_api


class DataList(list):
    ...


EnvName = str  # alias for better semantics


class MergeOperation:
    def __init__(self, key: str):
        self.key = key

    def run(self, key_container: dict | list) -> None:
        """Run the operation.

        Implementation should mutate the key's container.
        """


@dataclass
class SchemaTree:
    ...


T = TypeVar("T")


class Stack(Generic[T]):
    """Generic stack from mypy examples."""

    def __init__(self) -> None:
        self.items: list[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()

    def is_empty(self) -> bool:
        return not self.items

