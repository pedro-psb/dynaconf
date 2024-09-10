from __future__ import annotations

from dataclasses import dataclass, field

from .data_structs import DataDict
from .typing import Optional, SharedOptions

DataByEnv = dict[str, DataDict]
LoaderSpec = tuple[str, str]  # (loader_id, uri)


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
        self.loaded_data: dict[str, list[LoadedData]] = {}
        """Some description"""

    def load_resource(self, loader_id: str, uri: str) -> dict:
        """Load data from sources using registered loaders.

        Store and return a env-data map in the format: {env_name<str>: data<DataDict>}
        """
        return {}


@dataclass
class LoadedData:
    loader_id: str
    uri: str
    parsed_data: dict
    order: int


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
