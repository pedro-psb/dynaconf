from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from .data_structs import BaseOptions, DataDict

if TYPE_CHECKING:
    from .dynaconf_options import SharedOptions


@dataclass
class EnvOptions(BaseOptions):
    default_env_name: str = "default"
    strict_env_list: Optional[list[str]] = None


class EnvManager:
    def __init__(
        self, shared_options: SharedOptions, options: Optional[EnvOptions] = None
    ):
        opts = options or EnvOptions()

        self.active_env = opts.default_env_name
        self.options = opts
        self._env_datadict_map: dict[str, DataDict] = {opts.default_env_name: {}}

    def get(self, env_name: Optional[str] = None) -> DataDict:
        use_env = env_name or self.active_env
        return self._env_datadict_map[use_env]
