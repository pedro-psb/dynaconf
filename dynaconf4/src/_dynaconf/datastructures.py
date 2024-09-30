from __future__ import annotations
from typing import NamedTuple, Sequence, Optional, Callable, TypeVar, Generic
from _dynaconf.abstract import BaseOperation, BaseMergeTree
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _dynaconf.token_registry import Merge

TokenName = str
EnvName = str
T = TypeVar("T")


def is_token(value: str) -> bool:
    return isinstance(value, str) and value.startswith("@")


def ensure_path(path: TreePath | str) -> TreePath:
    def cast_int(s):
        try:
            return int(s)
        except ValueError:
            return s

    if isinstance(path, str):
        return TreePath([cast_int(val) for val in path.split(".")])
    return path

def ensure_rooted(_data: dict):
    if "root" not in _data.keys():
        return {"root": _data}
    return _data
        
# loader related

class Loader:
    read: Callable
    parse: Callable
    split_envs: Callable


class LoadRequest(NamedTuple):
    loader_id: str
    uri: str
    order: int = 0
    has_explicit_envs: Optional[bool] = None
    allowed_env_list: Optional[list] = None
    direct_data: Optional[dict] = None



# linear data structures

class LinearDataStructure(Generic[T]):
    def __init__(self):
        self._data = []

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def __repr__(self):
        return repr(self._data)


class Stack(LinearDataStructure[T]):
    def pop(self) -> T:
        return self._data.pop()

    def push(self, item: T):
        self._data.append(item)

    def reverse(self):
        self._data.reverse()


class Queue(LinearDataStructure):
    def dequeue(self):
        return self._data.pop(0)

    def enqueue(self, item):
        self._data.insert(0, item)

# trees related

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


class PartialToken(NamedTuple):
    id: str
    args: Optional[str]


class DynaconfToken(NamedTuple):
    id: str
    args: Optional[str]
    lazy: bool
    fn: Callable
    next: Optional[DynaconfToken]
    meta: bool = False


class TokenCallback(NamedTuple):
    fn: Callable
    lazy: bool = False


class MergeTree(BaseMergeTree):
    def __init__(
        self,
        merge_op_map: Optional[dict[TreePath | str, list[BaseOperation]]] = None,
        meta_token_map: Optional[dict[TreePath | str, list[DynaconfToken]]] = None,
    ):
        _merge_op_map = (
            {ensure_path(k): v for k, v in merge_op_map.items()}
            if merge_op_map
            else None
        )
        _meta_token_map = (
            {ensure_path(k): v for k, v in meta_token_map.items()}
            if meta_token_map
            else None
        )
        self._merge_operation_data: dict[TreePath, list[BaseOperation]] = (
            _merge_op_map or {}
        )
        self._meta_token_data: dict[TreePath, list[DynaconfToken]] = (
            _meta_token_map or {}
        )

    def get(self, path: TreePath | str) -> list[BaseOperation] | None:
        return self._merge_operation_data.get(ensure_path(path), None)

    def add(self, path, value):
        self._merge_operation_data.setdefault(path, [])
        self._merge_operation_data[path].append(value)

    def add_meta_token(self, path, token):
        self._meta_token_data.setdefault(path, [])
        self._meta_token_data[path].append(token)

    def get_meta_token(self, path: TreePath | str, token_id: Optional[str] = None):
        """Get a meta token related to a path.

        Returns a tuple of DynaconfTokens at this path, or one DynaconfToken if token_id is given.
        """
        meta_tokens = self._meta_token_data.get(ensure_path(path), [])
        if token_id:
            query = [it for it in meta_tokens if it.id == token_id]
            return query[0] if query else None
        return tuple(meta_tokens) if meta_tokens else tuple()

    def __eq__(self, o):
        return (
            self._merge_operation_data == o._merge_operation_data
            and self._meta_token_data == o._meta_token_data
        )


class MergeTree2(BaseMergeTree):
    """Example of doing a different implementation opaquely."""

    def __init__(self, root: Merge):
        self._tree = root

    def get(self, path: TreePath):
        def _get(p: tuple[str | int, ...]):
            if len(p) == 1:
                return self._tree.value["root"][p[-1]]
            return _get(p[:-1])[p[-1]]

        return _get(path)
