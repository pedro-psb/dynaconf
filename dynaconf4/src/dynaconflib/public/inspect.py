from dynaconflib.datastructures import DataDict, LoadRequest
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class DataNode:
    namespace: str
    path: list[str | int]
    key: str | int
    value: Any
    key_type: type
    value_type: type
    history: list[LoadRequest]


@dataclass
class InspectResult:
    keys: list[str]
    namespaces: list[str]
    nodes: list[DataNode]


def inspect_api(
    settings: DataDict,
    keys: Optional[list[str | int]] = None,
    namespaces: Optional[list[str]] = None,
) -> InspectResult:
    core = settings.__get_dynaconf__()

    keys = keys or []
    namespaces = namespaces or core.namespaces.get_current()

    result = []
    for ns, ns_state in core.namespaces.items():
        for path in keys:
            schema_node = core.schema.get(path)
            data_node = ns_state.get(path)
            # TODO: handle if is DataDict|List or terminal value
            history = data_node.__node_metadata__["patched_keys"][path]
            result.append(
                DataNode(
                    path,
                    path[-1],
                    data_node,
                    schema_node.key_type,
                    schema_node.value_type,
                    history,
                )
            )
    return InspectResult(keys, namespaces, result)
