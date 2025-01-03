from __future__ import annotations
from .standard import Graph
from .schema import SchemaTree, SchemaNode
from .data import DataDict, DataList
from .load import LoadRequest
from typing import Any, NamedTuple, TYPE_CHECKING
from dynaconflib.utils import type_guard, container_items
from dynaconflib.exceptions import MergeError

if TYPE_CHECKING:
    from dynaconflib.registry import PatchOpRegistry


class Patch(NamedTuple):
    operation_id: str
    path: list
    value: Any
    load_request: LoadRequest
    lazy: bool = False
    dependencies: list[Patch] = []


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

    def apply(self, base: DataDict, patch_list: list[Patch]):
        type_guard(patch_list, list)
        if not patch_list:
            return

        for patch in patch_list:
            prev_container_v = container_v = base
            schema_path = self.schema.get_path(from_raw=patch.path)
            # walk to get last container
            for i, node in enumerate(schema_path[:-1]):
                container_v = prev_container_v[node.key]
                prev_container_v = container_v
            # apply on last node
            operation: BasePatchOperation = self.registry.get(patch.operation_id)
            value = self.create_container_or_get_item(patch.value)
            try:
                operation.apply(container_v, schema_path[-1].key, value)
            except MergeError as e:
                raise MergeError(
                    f"{str(e)}\nFrom LoadRequest({patch.load_request.id_string()!r})."
                ) from e

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
