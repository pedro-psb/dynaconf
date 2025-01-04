from __future__ import annotations
import json
from typing import TYPE_CHECKING, Any
from dataclasses import dataclass, field, is_dataclass, asdict
from functools import partial
from enum import Enum
import rich

if TYPE_CHECKING:
    from dynaconflib.datastructures import DataDict, DataList


class SENTINEL(Enum):
    """Enum for sentinel/singleton values
    Recommended here: https://stackoverflow.com/a/76606310
    """

    empty = 0
    undefined_type = 1


Empty = SENTINEL.empty


def json_print(o):
    rich.print_json(json.dumps(o, cls=DynaconfJSONEncoder))


def rich_print(o):
    rich.print(o)


def node_history(node: DataDict | DataList) -> dict[str | int, list]:
    return node.__node_metadata__["patched_keys"]


def dump(o):
    support_dump = getattr(o, "dump", False)
    return o.dump() if support_dump else o


def xor(a, b) -> bool:
    return a and b or not (a or b)


def ensure_list(o: list[str | str]) -> list:
    return o if isinstance(o, list) else [o]


class DynaconfJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, Enum):
            return str(obj)
        if isinstance(obj, tuple) and hasattr(obj, "_asdict"):  # namedtuple
            breakpoint()
            return obj._asdict()
        if isinstance(obj, type):
            return str(obj)
        return super().default(obj)


def data_print(data: DataDict | DataList, format="json", debug=False):
    """Data print utilities.

    Params:
        data: The data to be displayed.
        format: The dumper used to print the data
        debug: Whether internal info should be displayed for debugging
    """
    # pretty json print
    if not debug:
        rich.print_json(json.dumps(data, indent=4, cls=DynaconfJSONEncoder))
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
            metadata["patched_keys"] = {
                k: [n.inspect() for n in v]
                for k, v in self.metadata["patched_keys"].items()
            }
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
    rich.print_json(
        json.dumps(root.to_compact_data(), indent=4, cls=DynaconfJSONEncoder)
    )


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
