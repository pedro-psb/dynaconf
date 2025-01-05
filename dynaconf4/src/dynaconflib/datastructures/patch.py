from __future__ import annotations
from .standard import Graph
from .schema import SchemaTree, SchemaNode
from .data import DataDict, DataList
from .load import LoadRequest
from typing import Any, NamedTuple, TYPE_CHECKING
from dynaconflib.utils import type_guard, container_items, dump, VerboseLevel
from dynaconflib.exceptions import MergeError
from dataclasses import dataclass, asdict

if TYPE_CHECKING:
    from dynaconflib.registry import PatchOpRegistry


class New: ...


@dataclass
class Patch:
    operation: str
    path: list
    value: Any
    load_request: LoadRequest
    lazy: bool = False

    def inspect(self):
        """Return data for inspect dump."""
        data = asdict(self)
        data["path"] = "/" + "/".join(self.path)
        data["load_request"] = self.load_request.inspect()
        return data

    def __json_encode__(self):
        if VerboseLevel.get() == VerboseLevel.MINIMAL:
            return {
                "operation": self.operation,
                # "path": "/".join([repr(n) for n in self.path]),
                "path": repr(self.path),
                "value": self.value,
                "load_identifier": self.load_request.id_string(),
            }
        return asdict(self)


class BasePatchOperation:
    def apply(self, data: DataDict | DataList, key, value):
        type_guard(data, (DataDict, DataList))
        if isinstance(data, DataList):
            return self.on_list(data, key, value)
        elif isinstance(data, DataDict):
            return self.on_dict(data, key, value)

    def on_dict(self, data: dict, key, value):
        raise NotImplementedError()

    def on_list(self, data: list, key, value):
        raise NotImplementedError()

    def __repr__(self):
        return f"PatchOperation({self.__class__.__name__})"


class PatchEngine:
    def __init__(
        self,
        patch_registry: PatchOpRegistry,
        schema: SchemaTree,
    ):
        self.registry = patch_registry
        self.schema = schema
        self.created = 0
        self.applied = 0

    def apply(self, base: DataDict, patch_list: list[Patch]):
        type_guard(patch_list, list)
        if not patch_list:
            return

        for patch in patch_list:
            # get last container from path
            prev_container_v = container_v = last_container = base
            schema_path = self.schema.get_path(from_raw=patch.path)
            for i, node in enumerate(schema_path[:-1]):
                container_v = prev_container_v[node.key]
                last_container = prev_container_v  # for error repor only
                prev_container_v = container_v

            # apply on last node
            operation: BasePatchOperation = self.registry.get(patch.operation)
            final_key = schema_path[-1].key
            value = self.create_container_or_get_item(patch.value)
            try:
                operation.apply(container_v, final_key, value)
            except Exception as e:
                raise MergeError(
                    f"{repr(e)}\n"
                    f"From patch={patch.__json_encode__()}\n"
                    f"Into container={container_v!r}\n"
                    f"Previous container={last_container!r}"
                ) from e

            # update container inspect info
            container_v.__node_metadata__["patched_keys"][final_key].append(patch)
        self.applied += 1

    def create(self, data: dict, load_request: LoadRequest) -> list[Patch]:
        type_guard(data, dict)
        final: list[Patch] = []

        def walk(container: dict | list, container_path: list):
            for k, v in container_items(container):
                path = container_path + [k]
                v_type = type(v)
                if v_type in (dict, list):
                    patch = Patch("add", path, v_type, load_request)
                    final.append(patch)
                    walk(v, path)
                else:
                    patch = Patch("replace", path, v, load_request)
                    final.append(patch)

        walk(container=data, container_path=[])
        self.created += len(final)
        return final

    def create_container_or_get_item(self, value):
        new_value = value
        if isinstance(value, type):
            if value is dict:
                new_value = DataDict()
            elif value is list:
                new_value = DataList()
            else:
                raise ValueError(
                    f"Schema container types must be dict or list. Got {value}"
                )
        return new_value

    def __json_encode__(self):
        return {
            "class": self.__class__.__name__,
            "created": self.created,
            "applied": self.applied,
        }
