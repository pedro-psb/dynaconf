"""
Main control module of dynaconf.

DynaconfCore manages global states and control the data flow in NamespaceSet.


## Overview Workflow

This is an overview of the main data organization.
(The names are not supposed to match the implementation)

* Core:
    * LoadRequestQ
    * Namespaces:
        * Namespace-0:
            * LoadedQ
            * PatchQ
            * LazyPatchQ
        * (...)
        * Namespace-k:
            * LoadedQ
            * PatchQ
            * LazyPatchQ


## Load Workflow

The core holds the LoadRequest Queue and is responsible for calling the
correct loader and distributing the data into the correct namespaces (ns).
It also holds several Registries for loaders, patch_operations, etc.

                                         ----> (ns-0) LoadedQ
                                        |         .
(core) LoadRequestQ -- load_pending() --|         .
                                        |         .
                                         ----> (ns-n) LoadedQ

## Merge Workflow

Each namespace is represented by a NamespaceState, which holds queues
for pending intermediary datastructures, like loaded data (but not merged),
patches ready to be applied and lazy patches, that should be applied later.

In this step, tokens, converteres and dynamic values are evaluated when
possible or moved to the lazyQ.

     namespace-k
    +------------------------------------------------+
    | base: DataDict                                 |
    |                                                |
    |    pending_loaded Q                            |
    |          |                                     |
    |          | create_patch(loaded) -> Patch       |
    |          |                                     |
    |    pending_patch Q                             |
    |          |                                     |
    |          | apply_patch(base, Patch) -> Patch   |
    |          |                                     |
    |  pending_patch_lazy Q                          |
    |          |                                     |
    |          | apply_lazy_patch(base, Patch)       |
    |          x                                     |
    +------------------------------------------------+


## Default System

The 'default' namespace (ns-default) always exist and it's content is the access-time
fallback for when the activate namespace doesnt contain the requested key. The system
is a simple implementation of a ChainMap using dynaconf internals.

The ns-default content comes first from the schema declaration, then from loaded data.

Example:

    Given the namespace content:
    * ns-default = {'a': 0, 'b': 0}
    * ns-dev = {'a': 1}

    Then:
    ```python
    >>> settings['a']  # active env has the key, use its value
    1
    >>> settings['b']  # activate env dont have the key, try ns-default
    0
    >>> settings['c']  # ns-default doesnt have it either
    KeyError: ...
    ```
"""

from __future__ import annotations
from dynaconflib.datastructures import (
    DataDict,
    LoadRequest,
    Patch,
    LoadContext,
    SchemaTree,
    PatchEngine,
)
from dynaconflib.registry import RegistrySet
from dynaconflib.utils import type_guard, raise_if, setup_limit
from typing import Optional
from dynaconflib.exceptions import UnknownNamespace
from enum import Enum, auto
from contextlib import contextmanager


Count = Optional[int | type[all]]


class CoreStatus(Enum):
    WAITING = auto()
    LOADING = auto()
    MERGING = auto()


class DynaconfCore:
    STATUS_SET = CoreStatus

    def __init__(self, id: str, schema: SchemaTree):
        # common
        self.id = id
        self.schema = schema
        self.registries = RegistrySet().setup_builtin()
        self.namespaces = NamespaceSet(self.registries)
        self.status = self.STATUS_SET.WAITING
        # load
        self.load_context = LoadContext(schema_tree=self.schema)
        self.pending_load_request: list[LoadRequest] = []
        # merge
        self.patch_engine = PatchEngine(self.registries.patch_operations, self.schema)

    def enqueue(self, *, load_request: LoadRequest):
        self.pending_load_request.append(load_request)

    def process_api(
        self,
        load: Count = None,
        merge: Count = None,
        merge_lazy: Count = None,
        namespaces=all,
    ):
        """Command API that control ingestion process.

        Params:
            load: Load all or the specified number of processing-units.
            merge: Merge all or the specified number of processing-units.
            merge_lazy: Merge all or the specified number of lazy processing-units.
            namespaces: The namespaces that should be used in the process.
        """
        namespaces = self.namespaces.filter(namespaces)
        load_limit = setup_limit(load)
        merge_limit = setup_limit(merge)
        merge_lazy_limit = setup_limit(merge_lazy)

        # global.loadRequestQ -> ns.loadedQ
        queue_len = len(self.pending_load_request)
        for _ in range(min(queue_len, load_limit)):
            self._load(namespace_filter=namespaces)

        for ns_state in namespaces:
            # ns.LoadedQ -> ns.PatchQ -> ns.PatchLazyQ
            queue_len = len(ns_state.loaded_q)
            for _ in range(min(queue_len, merge_limit)):
                self._merge(ns_state)

            # ns.PatchLazyQ -> Done
            queue_len = len(ns_state.patch_lazy_q)
            for _ in range(min(queue_len, merge_lazy_limit)):
                self._merge_lazy(ns_state)

    def validate(self, namespace=None):
        """Validate data from namespace main data."""

    def get_preload_requests(self) -> list[LoadRequest]:
        """Get preload request from namespace's pending_loaded."""
        return []

    @contextmanager
    def status_context(self, status: CoreStatus):
        original = self.status
        try:
            self.status = status
            yield
        finally:
            self.status = original

    def _load(self, namespace_filter=None):
        """Load one pending requests and add to namespaces."""
        with self.status_context(self.STATUS_SET.LOADING):
            load_request = self.pending_load_request.pop()
            loader = self.registries.loaders.get(load_request.loader_id)
            result = loader.load(load_request, self.load_context)
            for ns, data_parts in result.items():
                self.namespaces.get(ns).enqueue_loaded(data_parts)

    def _merge(self, ns_state: NamespaceState):
        """Merge one item from ns.load_q into ns.main."""
        with self.status_context(self.STATUS_SET.MERGING):
            ns_state.process_loaded(self.patch_engine)
            ns_state.process_patches(self.patch_engine)
            self.namespaces.update_frontend()

    def _merge_lazy(self, ns_state: NamespaceState):
        """Merge one lazy item from ns.load_lazy_q into ns.main."""
        with self.status_context(self.STATUS_SET.MERGING):
            ns_state.process_patches_lazy()
            self.namespaces.update_frontend()

    def debug(self):
        s = "    "
        print(f"\n{self.pending_load_request=}")
        print("namespaces:")
        for k, ns in self.namespaces.items():
            print(f"{s}- {k}")
            print(f"{s*2}{ns.data=}")
            print(f"{s*2}{ns.loaded_q=}")
            print(f"{s*2}{ns.patch_q=}")
            print(f"{s*2}{ns.patch_lazy_q=}")


class NamespaceState:
    def __init__(self, name, registry_set: RegistrySet):
        # common
        self.name = name
        self.registry_set = registry_set
        self.data = DataDict()
        # pending queues
        self.loaded_q: list[dict] = []
        self.patch_q: list[Patch] = []
        self.patch_lazy_q: list[Patch] = []

    def enqueue_loaded(self, data_parts: list[dict]):
        self.loaded_q.extend(data_parts)

    def process_loaded(self, patch_engine: PatchEngine):
        """Process all data in pending_loaded or until limit is reached."""
        loaded_data = self.loaded_q.pop()
        patch_list = patch_engine.create(loaded_data)
        self.patch_q.extend(patch_list)

    def process_patches(self, patch_engine: PatchEngine):
        patches = []
        while self.patch_q:
            if not self.patch_q[-1].lazy:
                patches.append(self.patch_q.pop(0))
        patch_engine.apply(self.data, patches)

    def process_patches_lazy(self): ...

    def validate(self): ...

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.data=})"


class NamespaceSet:
    def __init__(self, registries: RegistrySet):
        self.current = "default"
        self.namespaces: dict[str, NamespaceState] = {
            "default": NamespaceState("default", registries),
            # TODO: consider using 'main' when namespaces are disabled, so
            # it we always have at least: ns-main + ns-default (fallback)
            # For now its not being used and default is also the main.
            "main": NamespaceState("main", registries),
            "_internal": NamespaceState("_internal", registries),
            "_frontend": NamespaceState("_frontend", registries),
        }

    def update_frontend(self):
        """Update the frontend namespace object."""
        front_ns = self.get("_frontend")
        front_ns.data.clear()
        current_ns = self.get()
        for k, v in current_ns.data.items():
            front_ns.data[k] = v

    def get(self, namespace=None) -> NamespaceState:
        namespace = namespace or self.current
        return self.namespaces[namespace]

    def filter(self, namespaces: list[str] | type[all]) -> list[NamespaceState]:
        if namespaces is all:
            return [self.get(ns_k) for ns_k in self.keys()]

        # validate and filter
        for ns_k in namespaces:
            self.exists(ns_k, raises=True)
        return [self.get(ns_k) for ns_k in namespaces]

    def exists(self, namespace: str, raises=True) -> bool:
        if namespace not in self.keys():
            if raises:
                raise UnknownNamespace()
            return False
        return True

    def set_current_namespace(self, namespace: str):
        if namespace not in self.namespaces:
            raise KeyError(f"Namespace doesn't exist: {namespace}")
        self.current = namespace

    def items(self):
        return self.namespaces.items()

    def keys(self):
        return self.namespaces.keys()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.current=}, {self.namespaces=})"
