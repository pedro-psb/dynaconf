from __future__ import annotations
from typing import NamedTuple, Optional
from .schema import SchemaTree
from .standard import PriorityField
from collections import defaultdict
from dynaconflib.utils import type_guard
from dynaconflib.exceptions import LoadError
from dataclasses import dataclass, field, asdict


@dataclass
class LoadRequest:
    """
    Params:
        loader_id: The id of the loader to be used.
        uri: An unique identifier for the data source.
        order: The order that the request will be loaded.
        namespace_in_root: Whether the data source has namespaces in root.
        namespace_filter: Ignore namespaces not in the filter list.
        direct_data: Used for direct data loading.

    """

    loader_id: str
    uri: str
    priority_field: PriorityField = field(default_factory=PriorityField)
    namespace_in_root: bool = None
    namespace_filter: Optional[list] = None
    direct_data: Optional[dict] = None
    base_node: Optional[dict | list] = None

    def inspect(self) -> dict:
        return asdict(self)

    def id_string(self):
        return f"{self.loader_id}:{self.uri}"


class LoadContext(NamedTuple):
    namespace_main: str = "main"
    namespace_in_root: bool = False
    namespace_filter: list[str] = None
    envvar_prefix: str = None
    schema_strict: bool = True
    schema_tree: SchemaTree = None
    schema_strict: bool = True
    case_all_lower: bool = True


class LoadResult:
    """
    The result of a load.

    It hold a list of load-parts [0] and provides access to the data by namespace [1].
    Most loaders only contain one load-part, but some requires multi-part, like
    multi-file yaml and the environ loader.

    [0]: load-part = { namespace-0: data, ..., namespace-n: data }
    [1]: result.get("namespace-0") -> [{ns-data}, ..., {ns-data}]

    Example:
        ```python
        [
            {"ns-0": data-0, ..., "ns-k": data-k},  # part 0 with ns-0 to ns-k
            ...
            {"ns-0": data-0, "ns-1": data-1},  # part n with ns-0 and ns-1
        ]
        ```
    """

    def __init__(
        self,
        data_parts: list[dict],
        load_request: LoadRequest,
        load_context: LoadContext,
    ):
        # init
        self.load_request = load_request
        self._data_by_ns = defaultdict(list)
        self.data = []
        # ensure namespaces
        namespace_in_root = (
            load_request.namespace_in_root or load_context.namespace_in_root
        )
        namespace_main = load_context.namespace_main
        for data_part in data_parts:
            if namespace_in_root is True:
                data_part = {env: data for env, data in data_part.items()}
            else:
                data_part = {namespace_main: data_part}
            self.add(data_part)

    def add(self, data_part):
        self.data.append(data_part)
        for env, data in data_part.items():
            try:
                type_guard(data, dict)
            except TypeError:
                raise LoadError(
                    f"Malformed part-data. Expected {dict}, got {type(data)}.\n{self.load_request=}"
                )
            self._data_by_ns[env].append(data)

    def get(self, ns: str) -> list[dict]:
        return self._data_by_ns[ns]

    def items(self) -> list[tuple[str, dict]]:
        return self._data_by_ns.items()

    def __repr__(self):
        return repr(self._data_by_ns)


class LoadDeclaration:
    """Base class for creating LoadRequests with a convenient user API."""

    def __init__(self):
        self.load_requests: list[LoadRequest] = []

    def __iter__(self):
        yield from self.load_requests


class BaseLoader:
    def __init__(self, id: str):
        self.id = id

    def load(
        self, load_request: LoadRequest, load_context: LoadContext, **kwargs
    ) -> LoadResult:
        raise NotImplementedError()
