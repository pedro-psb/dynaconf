from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple, Optional
from typing import TypeVar, Generic

import rich


class BaseOptions:
    def print(self):
        rich.print(self)


class DataDict(dict): ...


class DataList(list): ...


EnvName = str  # alias for better semantics


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


@dataclass
class SchemaTree: ...


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


class LoadRequest(NamedTuple):
    loader_id: str
    uri: str
    order: int = 0
    has_explicit_envs: Optional[bool] = None
    data: Optional[dict] = None


class LoadResponse(NamedTuple): ...


@dataclass
class DynaconfToken:
    """Represent a dynaconf string, such as "@json variable".

    Params:
        token_id:
            The token name identifier. Used to relate to a specific token hanlder function.
        arg_list:
            List of arguments (possibly empty) of the dynaconf string. E.g:
            In "@insert 1 foo", arg_list=[1].
        next_token:
            The next token in the chain in evaluation order (right-left). E.g:
            In "@is_even @int 12", `DynaconfToken("int", ..., next_token=DynaconfToken("is_even", ...))`.
    """

    token_id: str
    arg_list: list
    next_token: DynaconfToken


@dataclass
class DynaconfTree:
    """A tree wrapper to provide convenient and efficient manipulation of a DataDict/DataList tree.

    Params:
        root:
            A DataDict instance. Its subtrees are composed of DataDict or DataList and they should contain
            node-level metadata about merging, lazy-eval and validation.
        lazy_cache_map:
            Maps key names which contains lazy values with it's container object.
    """

    root: DataDict
    lazy_cache_map: dict[str, DataDict] = field(default_factory=dict)
