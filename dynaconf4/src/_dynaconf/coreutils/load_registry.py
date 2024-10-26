from typing import Any, Callable

from _dynaconf.abstract import BaseLoadRegistry, BaseSchemaTree
from _dynaconf.datastructures import Loader, LoadRequest, TreePath, LoadContext
from .load import split_envs


class LoaderRegistry(BaseLoadRegistry):
    def __init__(self):
        self._loaders = {
            "builtin.direct": load_direct,
            "builtin.environ": load_environ,
        }

    def get_loader(self, loader_id: str) -> Loader:
        loader = self._loaders.get(loader_id)
        if not loader:
            raise RuntimeError(f"No TokenCallback registered for token: {loader_id!r}")
        return loader


# builtin loaders


def load_direct(load_request: LoadRequest, load_context: LoadContext):
    return load_request.direct_data


def load_environ(load_request: LoadRequest, load_context: LoadContext):
    import os

    schema_tree = load_context.schema_tree
    prefix = "dynaconf_"
    strict_lower = True

    def cast_int(k):
        try:
            return int(k)
        except TypeError:
            raise

    def process_key(string_key: str) -> TreePath:
        keys = []
        # strip PREFIX_ and split on separator
        raw_keys = string_key[len(prefix) :].split("__")
        keys.append(raw_keys[0].lower())
        for i in range(1, len(raw_keys)):
            cur_key = raw_keys[i]
            prev_key = raw_keys[i-1]
            key = cast_int(cur_key) if schema_tree.get_key_type(*raw_keys[:i]) is list else cur_key.lower()
            keys.append(key)
        return TreePath(keys)

    def process_value(value: str) -> Any:
        return value

    def treefy_map(data_map: list[tuple[TreePath, Any]]) -> dict[str | int, Any]:
        root = {}
        def add_to_tree(container, keys, value):
            if len(keys) < 2:
                container[keys[0]] = value
                return
            cur = keys[0]
            next = keys[1]
            next_container = [None] if isinstance(next, int) else {}
            container[cur] = next_container
            add_to_tree(next_container, keys[:1], value)

        # breakpoint()
        for keys, value in data_map:
            add_to_tree(root, keys, value)
        return root

    path_value_map = [
        (process_key(k), process_value(v))
        for k, v in os.environ.items()
        if k.lower().startswith(prefix)
    ]
    return treefy_map(path_value_map)


def load_toml(load_request: LoadRequest, load_context: LoadContext): ...


def load_json(load_request: LoadRequest, load_context: LoadContext): ...


def load_yaml(load_request: LoadRequest, load_context: LoadContext): ...
