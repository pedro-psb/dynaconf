from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from .builtin.loaders import DirectLoader, EnvironLoader, SqliteLoader, TomlLoader
from .data_structs import EnvName
from _dynaconf.datastructures import LoadRequest

from .hookspec import ResourceLoader

if TYPE_CHECKING:
    from .dynaconf_options import SharedOptions


@dataclass
class SimpleLoad:
    enabled: bool = True
    load_from_env_last: bool = True


@dataclass
class LoadingOptions:
    simple_startup: SimpleLoad = field(default_factory=SimpleLoad)
    cache_loaded_data: bool = False


class LoadingManager:
    def __init__(
        self,
        shared_options: SharedOptions,
        options: Optional[LoadingOptions] = None,
    ):
        # config
        self.shared_options = shared_options
        self.options = options or LoadingOptions()

        # plugins
        self.loader_registry: dict[str, ResourceLoader] = {
            "builtin.loaders.direct": DirectLoader(),
            "builtin.loaders.toml": TomlLoader(),
            "builtin.loaders.environ": EnvironLoader(),
            "builtin.loaders.sqlite": SqliteLoader(),
        }

        # state
        self.loaded_data_cache: dict[LoadRequest, dict[EnvName, dict]]
        """The cache of raw data that was effectively loaded for each env."""

        self.env_names: set[str] = set()
        """The list of name that were effectively loaded."""

    def add_loader(self, loader_id: str, loader_instance: ResourceLoader):
        if loader_id in self.loader_registry:
            raise ValueError(
                "Unique constrain error: The loader with id='{}' already exists."
            )

        self.loader_registry[loader_id] = loader_instance

    def load_resource(self, load_request: LoadRequest) -> dict[EnvName, dict]:
        """Load data from sources using registered loaders.

        The loaded data is split into environemnts, optionally saved to loaded cache
        and IS NOT processed.

        Returns:
            An env-data map in the format: {env_name<str>: data<dict>}
        """
        loader = self.loader_registry[load_request.loader_id]
        has_explicit_envs = load_request.has_explicit_envs or loader.has_explicit_envs
        allowed_envs = load_request.allowed_env_list
        used_envs = []

        # loading pipeline
        raw_bytes = loader.read(load_request.uri)
        parsed_data = loader.parse(raw_bytes, data=load_request.direct_data)
        env_data_map = loader.split_envs(
            parsed_data,
            has_explicit_envs=has_explicit_envs,
            default_env=self.shared_options.default_env_name,
        )

        # optional env filtering
        used_envs = allowed_envs or list(env_data_map.keys())
        if allowed_envs:
            env_data_map = {env:data for env,data in env_data_map.items() if env in allowed_envs}

        # state update
        for env in used_envs:
            self.env_names.add(env.lower())

        if self.options.cache_loaded_data:
            self.loaded_data_cache[load_request] = env_data_map

        return env_data_map

    def debug(self):
        """Print useful debuggin info.

        TODO make the data JSON serializable to use json.dumps(o, indent=4).
        The readability is so much better.
        """
        import rich

        rich.print("\nloader_registry:")
        rich.print(self.loader_registry)
        rich.print("\loaded_data_cache:")
        rich.print(self.loaded_data_cache)


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
    raise NotImplementedError()
