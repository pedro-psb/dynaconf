from __future__ import annotations
from graphlib import TopologicalSorter
from typing import Generic, TypeVar, Set, Dict, List, Optional, Tuple, Sequence
from heapq import heappush, heappop
from dataclasses import dataclass
from enum import IntEnum


T = TypeVar("T")

# Linear


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


class Queue(LinearDataStructure[T]):
    def push(self, item) -> T | None:
        self._data.insert(0, item)

    def pop(self):
        try:
            return self._data.pop(0)
        except IndexError:
            return None


class PriorityGroup(IntEnum):
    GREEN = 0
    ORANGE = 1
    RED = 2


@dataclass
class PriorityField:
    priority: int = 0
    group: PriorityGroup = PriorityGroup.GREEN


class PriorityQueue(Generic[T]):
    PRIORITY_GROUP_SET = PriorityGroup
    ITEM_POSITION = 3  # in queue tuple

    def __init__(self):
        self._queue: List[Tuple[int, int, T]] = []
        self._index: int = 0

    def push(self, item: T) -> None:
        try:
            group = item.priority_field.group
            priority = item.priority_field.priority
        except AttributeError:
            raise RuntimeError(
                "PriorityQueue items should have an attribute 'priority_field: PriorityField'."
            )
        heappush(self._queue, (-group, -priority, self._index, item))
        self._index += 1

    def pop(self) -> Optional[T]:
        if not self._queue:
            return None
        return heappop(self._queue)[self.ITEM_POSITION]

    def peek(self) -> Optional[T]:
        if not self._queue:
            return None
        return self._queue[0][self.ITEM_POSITION]

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def copy(self):
        return self.__copy__()

    def __contains__(self, item: T) -> bool:
        return any(ituple[self.ITEM_POSITION] == item for ituple in self._queue)

    def __copy__(self):
        copy = PriorityQueue()
        copy._queue = self._queue.copy()
        copy._index = self._index
        return copy

    def __iter__(self):
        yield from (self.copy().pop() for _ in range(len(self)))

    def __len__(self) -> int:
        return len(self._queue)

    def __repr__(self):
        return f"{self.__class__.__name__}({list(self)})"


# Graphs


class Graph(Generic[T]):
    def __init__(self):
        self.graph: Dict[T, Set[T]] = {}

    def add_node(self, node: T) -> None:
        if node not in self.graph:
            self.graph[node] = set()

    def add_edge(self, source: T, target: T) -> None:
        self.add_node(source)
        self.add_node(target)
        self.graph[source].add(target)

    def topological_sort(self) -> List[T]:
        ts = TopologicalSorter(self.graph)
        try:
            return list(ts.static_order())
        except Exception:
            raise ValueError("Graph contains a cycle")

    def get_dependencies(self, node: T) -> Set[T]:
        if node not in self.graph:
            return set()

        deps = set()

        def collect_deps(n: T) -> None:
            for dep in self.graph[n]:
                deps.add(dep)
                collect_deps(dep)

        collect_deps(node)
        return deps


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
