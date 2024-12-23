from __future__ import annotations
from typing import NamedTuple, Optional, TYPE_CHECKING
from .schema import SchemaTree

if TYPE_CHECKING:
    from dynaconflib.registry import LoaderRegistry


class LoadRequest(NamedTuple):
    """
    Params:
        loader_id: The id of the loader to be used.
        uri: An unique identifier for the data source.
        order: The order that the request will be loaded.
        namespace_in_root: Whether the data source has namespaces in root.

    """

    loader_id: str
    uri: str
    order: int = 0
    namespace_in_root: bool = None
    namespace_filter: Optional[list] = None
    direct_data: Optional[dict] = None

    def load(self, registry: LoaderRegistry, context: LoadContext):
        loader = registry.get(self.loader_id)
        namespace_in_root = self.namespace_in_root or context.namespace_in_root
        parsed = loader.load(self, context)
        result = loader.ensure_namespaces(
            parsed,
            namespace_in_root=namespace_in_root,
            namespace_default=context.namespace_default,
        )
        return result


class LoadContext(NamedTuple):
    namespace_default: str = "default"
    namespace_in_root: bool = False
    namespace_filter: list[str] = None
    envvar_prefix: str = None
    schema_strict: bool = True
    schema_tree: SchemaTree = None
    schema_strict: bool = True


class BaseLoader:
    def __init__(self, id: str):
        self.id = id

    def load(self, load_request: LoadRequest, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def ensure_namespaces(
        parsed_data: dict,
        namespace_in_root: bool,
        namespace_default: str,
    ):
        if namespace_in_root is True:
            return {env: data for env, data in parsed_data.items()}
        return {namespace_default: parsed_data}
