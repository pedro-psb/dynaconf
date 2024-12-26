from typing import Any
import os
from dynaconflib.datastructures import LoadRequest, LoadContext, TreePath, BaseLoader
from dynaconflib.registry import LoaderRegistry
from dynaconflib.utils import Empty, is_last
from dynaconflib.datastructures import SchemaTree, SchemaNode


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
        schema = load_context.schema_tree
        prefix = "dynaconf_"
        strict_lower = True

        filtered_envvars = (
            (k, v) for k, v in os.environ.items() if k.lower().startswith(prefix)
        )
        loaded_parts = []
        for k, v in filtered_envvars:
            raw_path = self.process_key(k, prefix)
            value = self.process_value(v)
            data = self.path_to_data(raw_path, value, schema)
            loaded_parts.append(data)
        return loaded_parts

    @staticmethod
    def process_key(input: str, prefix: str) -> TreePath:
        keys = []
        raw_keys = input[len(prefix) :].split("__")
        keys.append(raw_keys[0].lower())
        for i in range(1, len(raw_keys)):
            cur_key = raw_keys[i]
            key = cur_key
            keys.append(key)
        return TreePath(keys)

    @staticmethod
    def process_value(value: str) -> Any:
        return value

    @staticmethod
    def path_to_data(raw_path: list[str], value, schema: SchemaTree) -> dict:
        """
        Transform a path in the form (raw_path: value) to its expanded pyhton data.

        Example:
            path_to_data(["a", "b"]], value) -> {"a": {"b": value}}
        """
        schema_path = schema.raw_to_schema_path(raw_path)
        return EnvLoader.schema_path_to_data(schema_path, value)

    @staticmethod
    def schema_path_to_data(schema_path: list[SchemaNode], value) -> dict:
        """
        Transform a path in the form (schema_path: value) to its expanded pyhton data.

        Example:
            path_to_data([SchemaNode("a", ...), SchemaNode("b", ...)], value) -> {"a": {"b": value}}
        """
        terminal_value = value
        parent_v = {}
        final_data = parent_v

        for i, current_schema in enumerate(schema_path):
            current_type = current_schema.value_type
            current_k = current_schema.key
            current_v = (
                current_type() if not is_last(schema_path, i) else terminal_value
            )
            # fill parent_v to sufficient length if a list
            if isinstance(parent_v, list):
                current_k = current_k.value
                for i in range(current_k + 1):
                    parent_v.append(Empty)
            # add to parent (works for dict and lists)
            parent_v[current_k] = current_v
            # update
            parent_v = current_v
        return final_data


class TomlLoader(BaseLoader):
    def load(self, load_request: LoadRequest, load_context: LoadContext): ...


class JsonLoader(BaseLoader):
    def load(self, load_request: LoadRequest, load_context: LoadContext): ...


class YamlLoader(BaseLoader):
    def load(self, load_request: LoadRequest, load_context: LoadContext): ...
