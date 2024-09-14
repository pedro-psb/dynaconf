from __future__ import annotations

from dataclasses import dataclass, field

from .data_structs import DataDict, LoadRequest
from .typing import Optional, SharedOptions


@dataclass
class SimpleLoad:
    enabled: bool = True
    load_from_env_last: bool = True


@dataclass
class LoadingOptions:
    simple_startup: SimpleLoad = field(default_factory=SimpleLoad)


class LoadingManager:
    def __init__(
        self, shared_options: SharedOptions, options: Optional[LoadingOptions] = None
    ):
        self.shared_options = shared_options
        self.options = options or LoadingOptions()
        self.loader_registry: dict[str, ResourceLoader] = {}

        self.data_chain_by_env: dict[str, LoadedDataChain] = {}
        """Mapping of env to LoadedDataChain."""

    def load_resource(self, load_request: LoadRequest) -> dict:
        """Load data from sources using registered loaders.

        The loaded data is split into environemtns added to the env_data_map,
        which contains the stack of loaded data for each env.

        Returns:
            An env-data map in the format: {env_name<str>: data<DataDict>}
        """
        loader_id, uri, order = load_request

        # loading pipeline
        loader = self.loader_registry[loader_id]
        raw_bytes = loader.read(uri)
        parsed_data = loader.parse(raw_bytes)
        env_data_map = loader.split_envs(parsed_data)

        # add data to each env's LoadedDataChain
        for env, data in env_data_map.items():
            data_dict = DataDict(data)
            loaded_data = LoadedData(load_request, data_dict)
            self.data_chain_by_env[env].add(loaded_data)
        return env_data_map

    def pop_from_env(self, env: str) -> DataDict:
        return self.data_chain_by_env[env].pop()


@dataclass
class LoadedData:
    loader_spec: LoadRequest
    parsed_data: DataDict


class LoadedDataChain:
    def __init__(self):
        self.stack = []
        self.index = 0

    def add(self, loaded_data: LoadedData):
        """Add item to stack.

        TODO: handle sorting when loaders are run concurrently.
        """
        self.stack.append(loaded_data)
        self.index += 1

    def top(self) -> DataDict:
        return self.stack[self.index].parsed_data

    def pop(self) -> DataDict:
        """Virtually pops from the top of the stack.

        The loaded data is not removed from storate.
        """
        if not self.stack:
            raise ValueError("The stack is empty.")

        if self.index == 0:
            raise ValueError("All stack items were consumed.")
        return self.stack.pop().parsed_data

    def reset_index(self):
        self.index = len(self.stack) - 1


class ResourceLoader:
    """Core API for loading a resource."""

    LOADER_ID = "builtin.base"

    def read(self, uri: str) -> bytes:
        """Open/read the resource and return it's raw (bytes) data."""
        return b""

    def parse(self, raw_bytes: bytes) -> dict:
        """Parse a raw (bytes) data and return its parsed data (dict, list and native types)."""
        return {}

    def split_envs(self, parsed_data: dict) -> dict[str, dict]:
        """Split the parsed data into environments {env: data}."""
        return {"production": {"key": "value"}}


def BatchLoader(*args, **kwargs) -> list[ResourceLoader]:
    """Convenience API to return multiple ResourceLoader from a simple user input.

    Implementation should contain custom logic to produce the list of ResourceLoader.

    Example:
        ```python
        >>> FileLoader("my/config_dir/*.yml")
        [YmlLoader("my/config_dir/file1.yml"),
                   YmlLoader("my/config_dir/file-2.yml"), ...]
        ```
    """
    return
