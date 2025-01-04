from __future__ import annotations
from dynaconflib.datastructures import DataDict, Patch
from dynaconflib.utils import (
    DynaconfJSONEncoder,
    container_items,
    node_history,
    json_print,
)
from dataclasses import dataclass, asdict
from typing import Optional, Any, TYPE_CHECKING
from functools import partial
import json

if TYPE_CHECKING:
    from dynaconflib.core import NamespaceState


@dataclass
class DataNode:
    path: list[str | int]
    key: str | int
    key_type: type
    value: Any
    value_type: type
    namespace: str
    child_patches: list[Patch]


@dataclass
class InspectResult:
    keys: list[str]
    namespaces: list[str]
    nodes: list[DataNode]

    def print(self, json=True):
        if json is True:
            json_print(self)
        else:
            print(self)

    def dump(self) -> dict:
        result = asdict(self)
        return json.dumps(result, indent=4, cls=DynaconfJSONEncoder)


def inspect_api(
    settings: DataDict,
    keys: Optional[list[str | int]] = None,
    namespaces: Optional[list[str]] = None,
    terminal_only: Optional[bool] = None,
) -> InspectResult:
    core = settings.__get_dynaconf__()

    terminal_only = terminal_only or True
    keys = keys or None
    namespaces = core.namespaces.filter(namespaces) or [core.namespaces.get_current()]
    ns_names = [ns.name for ns in namespaces]

    nodes = []
    for ns in namespaces:
        ns_nodes = get_nodes(ns, terminal_only)
        nodes.extend(ns_nodes)
    return InspectResult(keys, ns_names, nodes)


def get_nodes(namespace: NamespaceState, terminal_only):
    def is_terminal(v):
        return False if isinstance(v, (dict, list)) else True

    settings = namespace.data
    ns_name = namespace.name
    nodes = []

    def walk(node, path):
        for k, v in container_items(node):
            # filters
            if terminal_only and not is_terminal(v):
                continue

            # create inspect node
            new_path = path + (k,)
            new_node = partial(
                DataNode,
                path=path,
                key=k,
                key_type=type(k),
                value=v,
                value_type=type(v),
                namespace=ns_name,
            )
            if isinstance(v, (dict, list)):
                _history = node_history(v)
                nodes.append(new_node(child_patches=_history))
                walk(v, new_path)
            else:
                _history = {"__self__": node_history(node).get(k)}
                nodes.append(new_node(child_patches=_history))

    walk(settings, tuple())
    return nodes
