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
    PriorityQueue,
    PriorityField,
)
from dynaconflib.registry import RegistrySet
from dynaconflib.utils import (
    type_guard,
    raise_if,
    setup_limit,
    data_print,
    container_items,
)
from typing import Optional
from dynaconflib.exceptions import UnknownNamespace
from enum import Enum, auto
from contextlib import contextmanager


Count = Optional[int | type[all]]


class CoreStatus(Enum):
    """Status of the core instance.

    This is important for DataDict|DataList getters and setters, as these have
    different behavior if the caller is external (user) or internal (core).
    """

    WAITING = auto()
    LOADING = auto()
    MERGING = auto()


class DynaconfCore:
    STATUS_SET = CoreStatus

    def __init__(self, id: str, schema: Optional[SchemaTree] = None):
        # common
        self.id = id
        self.status = self.STATUS_SET.WAITING
        self.schema = schema or SchemaTree()
        self.registries = RegistrySet().setup_builtin()
        patch_registry = self.registries.patch_operations
        self.patch_engine = PatchEngine(patch_registry, self.schema)
        self.namespaces = NamespaceSet(self.registries, self.patch_engine, self)
        # load
        self.load_context = LoadContext(
            schema_tree=self.schema, schema_strict=self.schema.strict
        )
        self.load_request_q = PriorityQueue[LoadRequest]()

    def enqueue(self, *, load_request: LoadRequest):
        """Enqueue load_request into load_request_q."""
        self.load_request_q.push(load_request)

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
        queue_len = len(self.load_request_q)
        for i in range(min(queue_len, load_limit)):
            self._load(namespace_filter=namespaces)

        for ns_state in namespaces:
            # ns.LoadedQ -> ns.PatchQ -> ns.PatchLazyQ
            queue_len = len(ns_state.loaded_q)
            for i in range(min(queue_len, merge_limit)):
                self._merge(ns_state)

            # ns.PatchLazyQ -> Done
            queue_len = len(ns_state.patch_lazy_q)
            for i in range(min(queue_len, merge_lazy_limit)):
                self._merge_lazy(ns_state)

    def validate(self, namespace=None):
        """Validate data from namespace main data."""

    def get_preload_requests(self) -> list[LoadRequest]:
        """Get preload request from namespace's pending_loaded."""
        return []

    def direct_ingest(self, uri: str, path: tuple[str], value):
        # TODO: add support for LoadRequest to take a path argument
        key = path[-1]
        load_request = LoadRequest("builtin.direct", uri, direct_data={key: value})
        self.enqueue(load_request=load_request)
        self.process_api(load=all, merge=all)

    @contextmanager
    def status_context(self, status: CoreStatus):
        original = self.status
        try:
            self.status = status
            yield
        finally:
            self.status = original

    def is_merging(self) -> bool:
        return self.status == self.STATUS_SET.MERGING

    def _load(self, namespace_filter=None):
        """Load one pending requests and add to namespaces."""
        with self.status_context(self.STATUS_SET.LOADING):
            load_request = self.load_request_q.pop()
            loader = self.registries.loaders.get(load_request.loader_id)
            result = loader.load(load_request, self.load_context)
            for ns, data_parts in result.items():
                self.namespaces.get(ns).enqueue(
                    loaded_parts=data_parts, load_request=load_request
                )

    def _merge(self, ns_state: NamespaceState):
        """Merge one item from ns.load_q into ns.main."""
        with self.status_context(self.STATUS_SET.MERGING):
            ns_state.process_loaded()
            ns_state.process_patch()
            self.namespaces.update_frontend()

    def _merge_lazy(self, ns_state: NamespaceState):
        """Merge one lazy item from ns.load_lazy_q into ns.main."""
        with self.status_context(self.STATUS_SET.MERGING):
            ns_state.process_patches_lazy()
            self.namespaces.update_frontend()

    def debug(self):
        s = "    "
        print(f"\n{self.load_request_q=}")
        print("namespaces:")
        for k, ns in self.namespaces.items():
            print(f"{s}- {k}")
            print(f"{s*2}{ns.data=}")
            print(f"{s*2}{ns.loaded_q=}")
            print(f"{s*2}{ns.patch_q=}")
            print(f"{s*2}{ns.patch_lazy_q=}")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id=}, {self.status})"


class NamespaceState:
    def __init__(
        self, name, registry_set: RegistrySet, patch_engine: PatchEngine, data: DataDict
    ):
        # common
        self.name = name
        self.registry_set = registry_set
        self.patch_engine = patch_engine
        self.data = data
        # pending queues
        self.loaded_q = PriorityQueue[ProcUnit]()
        self.patch_q = PriorityQueue[ProcUnit]()
        self.patch_lazy_q = PriorityQueue[ProcUnit]()

    def enqueue(self, *, loaded_parts: list[dict], load_request: LoadRequest):
        self.loaded_q.push(
            ProcUnit(loaded_parts, load_request, load_request.priority_field)
        )

    def process_loaded(self):
        """Process one ProcUnit from loaded_q."""
        if self.loaded_q.is_empty():
            return
        # get and process
        proc_unit = self.loaded_q.pop()
        loaded_parts = proc_unit.loaded
        all_patches = []
        for load_part in loaded_parts:
            all_patches.extend(self.patch_engine.create(load_part))
        # update processing unit
        patches_immediate = []
        patches_lazy = []
        for patch in all_patches:
            if patch.lazy is False:
                patches_immediate.append(patch)
            else:
                patches_lazy.append(patch)
        proc_unit.update(patches=patches_immediate, patches_lazy=patches_lazy)
        # update namespace queues
        self.patch_q.push(proc_unit)
        self.patch_lazy_q.push(proc_unit)

    def process_patch(self):
        """Process one ProcUnit from patch_q."""
        if self.patch_q.is_empty():
            return
        proc_unit = self.patch_q.pop()
        patches = proc_unit.patches
        self.patch_engine.apply(self.data, patches)
        proc_unit.patches.clear()

    def process_patches_lazy(self):
        """Process one ProcUnit from patch_lazy_q."""
        if self.patch_lazy_q.is_empty():
            return
        proc_unit = self.patch_lazy_q.pop()
        patches_lazy = proc_unit.patches_lazy
        self.patch_engine.apply(self.data, patches_lazy)

    def validate(self): ...

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name=}, {self.data=})"


class NamespaceSet:
    def __init__(
        self, registries: RegistrySet, patch_engine: PatchEngine, core: DynaconfCore
    ):
        self._current = "default"
        self.core = core
        self.patch_engine = patch_engine
        self.registries = registries
        self.namespaces: dict[str, NamespaceState] = {}

        # initial namespaces
        # TODO: consider using 'main' when namespaces are disabled, so
        # it we always have at least: ns-main + ns-default (fallback)
        # For now its not being used and default is also the main.
        self.create("default")
        self.create("main")

        # special namespaces
        # * _internal: Used for dynaconf dynamic internal settings
        # * _front-end: A reference to the user-facing settings object
        self.create("_internal")
        self.create("_frontend")

    def update_frontend(self):
        """Update the frontend namespace object with the active ns.data."""
        front_ns = self.get("_frontend")
        front_ns.data.clear()
        current_ns = self.get_current()

        # Ensure data dict metadata is consistent
        # Note:
        #     This could be done in the patching system, but it is already
        #     complex enough on its own. If perf impact is too bad, we should
        #     reconsider
        def walk(data, path):
            for k, v in container_items(data):
                new_path = path + (k,)
                if isinstance(v, (dict, list)):
                    v.__init_dynaconf__(self.core)
                    v.__node_metadata__["path"] = new_path
                    v.__node_metadata__["namespace"] = current_ns.name
                    walk(v, new_path)

        walk(current_ns.data, tuple())

        # shallow copy root level k,v
        for k, v in current_ns.data.items():
            front_ns.data[k] = v

    def create(self, name: str):
        if name in self.namespaces:
            raise KeyError("Namespace already exist.")
        data = DataDict()
        data.__init_dynaconf__(self.core)
        data.__node_metadata__["namespace"] = name
        data.__node_metadata__["path"] = tuple()
        self.namespaces[name] = NamespaceState(
            name, self.registries, self.patch_engine, data
        )

    def get_current(self) -> NamespaceState:
        return self.get(self._current)

    def get(self, namespace) -> NamespaceState:
        self.exists(namespace)
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

    def set_current(self, namespace: str):
        self.exists(namespace, raises=True)
        self._current = namespace

    def items(self):
        return self.namespaces.items()

    def keys(self):
        return self.namespaces.keys()

    def __repr__(self):
        return f"{self.__class__.__name__}({self._current=}, {self.namespaces=})"


class ProcUnit:
    def __init__(
        self,
        loaded: list[dict],
        load_request: LoadRequest,
        priority_field: PriorityField = PriorityField(),
    ):
        self.load_request = load_request
        self.loaded = loaded
        self.patches = []
        self.patches_lazy = []
        self.priority_field = priority_field

    def update(
        self,
        *,
        patches: Optional[list[Patch]] = None,
        patches_lazy: Optional[list[Patch]] = None,
    ):
        if patches:
            self.patches = patches
        if patches_lazy:
            self.patches_lazy = patches_lazy

    def is_done(self):
        return self.loaded and self.patches and self.patches_lazy

    def clear(self):
        self.load_request = None
        self.loaded.clear()
        self.patches.clear()
        self.patches_lazy.clear()

    def __repr__(self):
        return f"{self.__class__.__name__}(uri={self.load_request.uri!r}, {self.loaded=}, {self.patches=}, {self.patches_lazy=})"
