from __future__ import annotations
from .standard import Graph
from .schema import SchemaTree, SchemaNode
from typing import Any, NamedTuple, TYPE_CHECKING
from dynaconflib.utils import type_guard

if TYPE_CHECKING:
    from .data import DataDict
    from dynaconflib.registry import PatchOpRegistry


class Patch(NamedTuple):
    operation_id: str
    path: list
    value: Any
    lazy: bool = False
    dependencies: list[Patch] = []


class BasePatchOperation:
    def apply(self, data: DataDict | list, key, value):
        if isinstance(data, list):
            return self.on_list(data, key, value)
        elif isinstance(data, dict):
            return self.on_dict(data, key, value)
        else:
            raise TypeError("Can only apply patches to dicts or lists")

    def on_dict(self, data: dict, key, value):
        raise NotImplementedError()

    def on_list(self, data: list, key, value):
        raise NotImplementedError()


class PatchEngine:
    def __init__(
        self, patch_registry: PatchOpRegistry, schema: SchemaTree, schema_strict=None
    ):
        self.registry = patch_registry
        self.schema = schema
        self.schema_strict = schema_strict or False

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
            value = patch.value() if patch.value in (dict, list) else patch.value
            operation.apply(container_v, schema_path[-1].key, value)

    def create(self, data: dict) -> list[Patch]:
        type_guard(data, dict)
        final: list[Patch] = []

        def walk(container: dict | list, container_path: list):
            for k, v in self.container_items(container):
                path = container_path + [k]
                v_type = type(v)
                if v_type in (dict, list):
                    patch = Patch("add", path, v_type)
                    final.append(patch)
                    walk(v, path)
                else:
                    patch = Patch("replace", path, v)
                    final.append(patch)

        walk(container=data, container_path=[])
        return final

    @staticmethod
    def container_items(container: dict | list):
        if isinstance(container, dict):
            return container.items()
        elif isinstance(container, list):
            return enumerate(container)
        else:
            raise TypeError(f"Unsupported container type: {type(container)}")
