from __future__ import annotations
import json
from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from functools import partial

if TYPE_CHECKING:
    from dynaconflib.datastructures import DataDict, DataList
Empty = object()


def xor(a, b) -> bool:
    return a and b or not (a or b)


def data_print(data: DataDict | DataList, format="json", debug=False):
    """Data print utilities.

    Params:
        data: The data to be displayed.
        format: The dumper used to print the data
        debug: Whether internal info should be displayed for debugging
    """
    # pretty json print
    if not debug:
        print(json.dumps(data, indent=4))
        return

    # debug print
    @dataclass
    class Node:
        key: str
        key_type: str
        value_type: str
        metadata: dict
        children: list = field(default_factory=list)

        def to_compact_data(self):
            children = [
                v.to_compact_data() for v in self.children if isinstance(v, Node)
            ]
            metadata = {k: repr(v) for k, v in self.metadata.items()}
            data = {
                "compact_id": f"{self.key!r}, {self.key.__class__.__name__}, {self.value_type}",
                "metadata": metadata,
                "children": children,
            }
            return data

    def walk(data):
        children = []
        for k, v in container_items(data):
            if isinstance(v, (dict, list)):
                children.append(
                    Node(
                        key=k,
                        key_type=k.__class__.__name__,
                        value_type=v.__class__.__name__,
                        metadata=v.__node_metadata__,
                        children=walk(v),
                    )
                )
            else:
                children.append(data)
        return children

    root = Node(
        key="root",
        key_type="str",
        value_type=data.__class__.__name__,
        metadata=data.__node_metadata__,
        children=walk(data),
    )
    # print(root)
    print(json.dumps(root.to_compact_data(), indent=4))


data_debug = partial(data_print, debug=True)


def container_items(container: dict | list):
    if isinstance(container, dict):
        return container.items()
    elif isinstance(container, list):
        return enumerate(container)
    else:
        raise TypeError(f"Unsupported container type: {type(container)}")


def setup_limit(limit):
    """Use positive int or infinity limit."""
    limit = limit or 0
    n = float("inf") if limit is all else limit
    if n < 0:
        raise ValueError(f"Limit should be a positive int. Got {limit}.")
    return n


def raise_if(condition: bool, exception, e_args=None):
    if condition:
        raise exception()


def type_guard(obj, t: type | tuple[type]):
    if not isinstance(obj, t):
        raise TypeError(f"Expected {t}, got {type(obj)}")


def is_last(it, i):
    return i == len(it) - 1
