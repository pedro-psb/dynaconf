from typing import Generic, TypeVar

T = TypeVar("T")


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
