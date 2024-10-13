from typing import Optional


class ResourceLoader:
    """Core API for loading a resource."""

    LOADER_ID = "builtin.base"
    has_explicit_envs: bool = True

    def read(self, uri: str, data: Optional[dict] = None, **extra_args) -> bytes:
        """Open/read the resource and return it's raw (bytes) data."""
        raise NotImplementedError("This method should be implemented.")

    def parse(self, raw_bytes: bytes, **extra_args) -> dict:
        """Parse a raw (bytes) data and return its parsed data (dict, list and native types)."""
        raise NotImplementedError("This method should be implemented.")

    def split_envs(
        self, parsed_data: dict, has_explicit_envs: bool, default_env: str, **kwargs
    ) -> dict[str, dict]:
        """Split the parsed data into environments {env: data}."""
        raise NotImplementedError("This method should be implemented.")
