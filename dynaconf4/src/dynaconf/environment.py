from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from .data_structs import BaseOptions, DataDict, DynaconfTree, EnvName

if TYPE_CHECKING:
    from .dynaconf_options import SharedOptions


@dataclass
class EnvOptions(BaseOptions):
    env_names: list[str] = ["default", "dev", "prod"]
    strict_env_names: bool = True


class EnvManager:
    def __init__(
        self, shared_options: SharedOptions, options: Optional[EnvOptions] = None
    ):
        self.shared_options = shared_options
        self.options = options or EnvOptions()

        # state
        self.active_env = self.shared_options.default_env_name
        self.env_names: list[str] = []

        self._env_datadict_map: dict[EnvName, DynaconfTree] = {}
        for env in self.options.env_names:
            self.init_env(env)

    def get(self, env_name: Optional[str] = None) -> DynaconfTree:
        use_env = env_name or self.active_env
        return self._env_datadict_map[use_env]

    def init_env(self, env_name: str):
        if env_name in self._env_datadict_map:
            raise ValueError(f"Env already initiated: {env_name}")
        self._env_datadict_map[env_name] = DynaconfTree(root=DataDict())
