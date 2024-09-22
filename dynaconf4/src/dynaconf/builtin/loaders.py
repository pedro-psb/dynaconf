from typing import Optional

from ..hookspec import ResourceLoader


class DirectLoader(ResourceLoader):
    LOADER_ID = "direct"
    has_explicit_envs = False

    def read(self, uri: str): ...

    def parse(self, raw_bytes: bytes, data: Optional[dict] = None):
        if not data:
            raise ValueError(
                "To use the DirectLoader a non-empty data arg should be provded.."
            )
        return data

    def split_envs(
        self,
        parsed_data: dict,
        has_explicit_envs: bool,
        default_env: str,
    ):
        if has_explicit_envs is True:
            return {env: data for env, data in parsed_data.items()}
        return {default_env: parsed_data}


class TomlLoader(ResourceLoader):
    LOADER_ID = "toml"
    ...


class EnvironLoader(ResourceLoader):
    LOADER_ID = "environ"
    ...


class SqliteLoader(ResourceLoader):
    LOADER_ID = "sqlite"
    ...
