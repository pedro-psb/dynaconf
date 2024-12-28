from graphlib import TopologicalSorter
from typing import Generic, TypeVar, Set, Dict, List, Optional, Tuple
from heapq import heappush, heappop
from dataclasses import dataclass


T = TypeVar("T")


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


@dataclass
class Ordered:
    order: int


class PriorityQueue(Generic[T]):
    def __init__(self):
        self._queue: List[Tuple[int, int, T]] = []
        self._index: int = 0

    def push(self, item: T) -> None:
        heappush(self._queue, (item.order, self._index, item))
        self._index += 1

    def pop(self) -> Optional[T]:
        if not self._queue:
            return None
        return heappop(self._queue)[2]

    def peek(self) -> Optional[T]:
        if not self._queue:
            return None
        return self._queue[0][2]

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def __len__(self) -> int:
        return len(self._queue)
