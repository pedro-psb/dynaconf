from typing import Any, Callable

from _dynaconf.abstract import BaseLoadRegistry, BaseSchemaTree
from _dynaconf.datastructures import Loader, LoadRequest, SchemaTree, TreePath
from _dynaconf.load import split_envs


class LoadContext:
    default_env_name: str
    envvar_prefix: str
    allowed_envs: list[str]
    schema_tree: BaseSchemaTree
    only_schema_keys: bool = True


class LoaderRegistry(BaseLoadRegistry):
    def __init__(self):
        self.default_key

        self._loaders = {
            "builtin.direct": Loader(noop, noop, split_envs),
        }

    def get_loader(self, loader_id: str) -> Loader:
        loader = self._loaders.get(loader_id)
        if not loader:
            raise RuntimeError(f"No TokenCallback registered for token: {loader_id!r}")
        return loader


# builtin loaders


def noop(load_request: LoadRequest, load_context: LoadContext):
    return load_request.direct_data


def load_envvar(load_request: LoadRequest, load_context: LoadContext):
    import os

    def process_key(key: str) -> TreePath:
        raise NotImplementedError()

    def process_value(key: str) -> Any:
        raise NotImplementedError()

    def treefy_map(data_map: list[tuple[TreePath, Any]]) -> dict[str | int, Any]:
        raise NotImplementedError()

    dynaconf_data_map = [
        (process_key(k), process_value(v)) for k, v in os.environ.items()
    ]
    return treefy_map(dynaconf_data_map)


def load_toml(load_request: LoadRequest, load_context: LoadContext): ...


def load_json(load_request: LoadRequest, load_context: LoadContext): ...


def load_yaml(load_request: LoadRequest, load_context: LoadContext): ...
