"""
Main control module of dynaconf.

DynaconfCore manages global states and control the data flow in NamespaceSet.


## Load Workflow

The core holds the LoadRequest Queue and is responsible for calling the
correct loader and distributing the data into the correct namespaces (ns).

                                         ----> (ns-0) LoadedQ
                                        |         .
(core) LoadRequestQ -- load_pending() --|         .
                                        |         .
                                         ----> (ns-n) LoadedQ

"""

from __future__ import annotations
from dynaconflib.datastructures import (
    DataDict,
    LoadRequest,
    LoadResult,
    Patch,
    LoadContext,
    SchemaTree,
    PatchEngine,
)
from dynaconflib.registry import RegistrySet
from dynaconflib.utils import type_guard


class DynaconfCore:
    def __init__(self, id: str, schema: SchemaTree):
        # common
        self.id = id
        self.schema = schema
        self.registries = RegistrySet().setup_builtin()
        self.namespaces = NamespaceSet(self.registries)
        # load
        self.load_context = LoadContext(schema_tree=self.schema)
        self.pending_load_request: list[LoadRequest] = []
        # merge
        self.patch_engine = PatchEngine(self.registries.patch_operations, self.schema)

    def enqueue_load_request(self, load_request: LoadRequest):
        self.pending_load_request.append(load_request)

    def load_pending(self):
        """Load pending requests and add to namespaces."""
        # TODO handle strict and loose namespace
        # e.g, raise when unknown namespace is loaded or create if doesnt exist
        while self.pending_load_request:
            load_request = self.pending_load_request.pop()
            loader = self.registries.loaders.get(load_request.loader_id)
            result = loader.load(load_request, self.load_context)
            for ns, data_parts in result.items():
                self.namespaces.get(ns).enqueue_loaded(data_parts)

    def merge_pending(self, namespace=None):
        """Merge pending loaded data into namespace main data."""
        namespace_set = [namespace] if namespace else self.namespaces.keys()
        for namespace in namespace_set:
            ns_state = self.namespaces.get(namespace)
            ns_state.process_loaded(self.patch_engine)
            ns_state.process_patches(self.patch_engine)

    def evaluate_pending(self, namespace=None):
        """Evaluate pending loaded data into namespace main data."""
        namespace_set = [namespace] if namespace else self.namespaces.keys()
        for namespace in namespace_set:
            ns_state = self.namespaces.get(namespace)
            ns_state.process_patches_lazy()


class NamespaceState:
    def __init__(self, name, registry_set: RegistrySet):
        # common
        self.name = name
        self.registry_set = registry_set
        self.data = DataDict()
        # pending queues
        self.pending_loaded: list[dict] = []
        self.pending_patch: list[Patch] = []
        self.pending_patch_lazy: list[Patch] = []

    def enqueue_loaded(self, data_parts: list[dict]):
        self.pending_loaded.extend(data_parts)

    def process_loaded(self, patch_engine: PatchEngine):
        while self.pending_loaded:
            loaded_data = self.pending_loaded.pop()
            patch_list = patch_engine.create(loaded_data)
            self.pending_patch.extend(patch_list)

    def process_patches(self, patch_engine: PatchEngine):
        patches = []
        while self.pending_patch:
            if not self.pending_patch[-1].lazy:
                patches.append(self.pending_patch.pop(0))
        patch_engine.apply(self.data, patches)

    def process_patches_lazy(self): ...

    def validate(self): ...


class NamespaceSet:
    def __init__(self, registries: RegistrySet):
        self.current = "default"
        self.namespaces: dict[str, NamespaceState] = {
            "default": NamespaceState("default", registries),
            "_internal": NamespaceState("_internal", registries),
        }

    def get(self, namespace=None) -> NamespaceState:
        namespace = namespace or self.current
        return self.namespaces[namespace]

    def set_current_namespace(self, namespace: str):
        if namespace not in self.namespaces:
            raise KeyError(f"Namespace doesn't exist: {namespace}")
        self.current = namespace

    def items(self):
        return self.namespaces.items()

    def keys(self):
        return self.namespaces.keys()
