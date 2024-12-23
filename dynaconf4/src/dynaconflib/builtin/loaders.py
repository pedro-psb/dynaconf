from typing import Any
import os
from dynaconflib.datastructures import LoadRequest, LoadContext, TreePath, BaseLoader
from dynaconflib.registry import LoaderRegistry


def setup_loaders(registry: LoaderRegistry):
    registry.add("builtin.direct", DirectLoader("builtin.direct"))
    registry.add("builtin.environ", EnvLoader("builtin.environ"))
    registry.add("builtin.json", JsonLoader("builtin.json"))
    registry.add("builtin.toml", TomlLoader("builtin.toml"))
    registry.add("builtin.yaml", YamlLoader("builtin.yaml"))


class DirectLoader(BaseLoader):
    def load(self, load_request: LoadRequest, load_context: LoadContext):
        return load_request.direct_data


class EnvLoader(BaseLoader):
    def load(self, load_request: LoadRequest, load_context: LoadContext):
        schema_tree = load_context.schema_tree
        prefix = "dynaconf_"
        strict_lower = True

        path_value_map = [
            (self.process_key(k, prefix), self.process_value(v))
            for k, v in os.environ.items()
            if k.lower().startswith(prefix)
        ]
        return self.treefy_map(path_value_map)

    @staticmethod
    def process_key(input: str, prefix: str) -> TreePath:
        def cast_int(k):
            try:
                return int(k)
            except TypeError:
                raise

        keys = []
        # strip PREFIX_ and split on separator
        raw_keys = input[len(prefix) :].split("__")
        keys.append(raw_keys[0].lower())
        for i in range(1, len(raw_keys)):
            cur_key = raw_keys[i]
            prev_key = raw_keys[i - 1]
            # key = (
            #     cast_int(cur_key)
            #     if schema_tree.get_type(*raw_keys[:i]) is list
            #     else cur_key.lower()
            # )
            key = cur_key
            keys.append(key)
        return TreePath(keys)

    @staticmethod
    def process_value(value: str) -> Any:
        return value

    @staticmethod
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

        for keys, value in data_map:
            add_to_tree(root, keys, value)
        return root


class TomlLoader(BaseLoader):
    def load(self, load_request: LoadRequest, load_context: LoadContext): ...


class JsonLoader(BaseLoader):
    def load(self, load_request: LoadRequest, load_context: LoadContext): ...


class YamlLoader(BaseLoader):
    def load(self, load_request: LoadRequest, load_context: LoadContext): ...
