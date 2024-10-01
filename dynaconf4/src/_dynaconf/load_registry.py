from typing import Any, Callable

from _dynaconf.abstract import BaseLoadRegistry, BaseSchemaTree
from _dynaconf.datastructures import Loader, LoadRequest, TreePath, LoadContext
from _dynaconf.load import split_envs


class LoaderRegistry(BaseLoadRegistry):
    def __init__(self):
        self._loaders = {
            "builtin.direct": load_direct,
        }

    def get_loader(self, loader_id: str) -> Loader:
        loader = self._loaders.get(loader_id)
        if not loader:
            raise RuntimeError(f"No TokenCallback registered for token: {loader_id!r}")
        return loader


# builtin loaders


def load_direct(load_request: LoadRequest, load_context: LoadContext):
    return load_request.direct_data


def load_envvar(load_request: LoadRequest, load_context: LoadContext):
    import os

    schema_tree = load_context.schema_tree

    def cast_int(k):
        try:
            return int(k)
        except TypeError:
            raise

    def process_key(key: str) -> TreePath:
        keys = []
        for k in key.split():
            _k = cast_int(k) if schema_tree.get_key_type(k) is int else k
            keys.append(_k)
        return TreePath(keys)

    def process_value(key: str) -> Any:
        raise NotImplementedError()

    def treefy_map(data_map: list[tuple[TreePath, Any]]) -> dict[str | int, Any]:
        tree = {}

        def add_to_tree(keys, value):
            # Recursively build the tree structure
            for key in keys[:-1]:
                tree = tree.setdefault(key, {})
            tree[keys[-1]] = value

        for keys, value in data_map:
            add_to_tree(keys, value)
        return tree

    dynaconf_data_map = [
        (process_key(k), process_value(v)) for k, v in os.environ.items()
    ]
    return treefy_map(dynaconf_data_map)


def load_toml(load_request: LoadRequest, load_context: LoadContext): ...


def load_json(load_request: LoadRequest, load_context: LoadContext): ...


def load_yaml(load_request: LoadRequest, load_context: LoadContext): ...
