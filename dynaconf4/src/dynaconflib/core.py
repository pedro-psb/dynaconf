from typing import Iterable
from .datastructures import DataDict, DataList, DataPatch, LoadRequest
from .registry import Registry


class EnvState:
    # shared registries
    loaders_reg = Registry("loaders", noop)
    token_callbacks_reg = Registry("token_callbacks", noop)
    merge_operations_reg = Registry("merge_operations", noop)
    validator_reg = Registry("validators", noop)

    def __init__(self, name):
        self.name = name
        self.data = None
        self.pending_load_request: list[LoadRequest] = []
        self.pending_patch_create: list[DataDict] = []
        self.pending_patch_apply: list[DataPatch] = []

    def load_pending(self): ...

    def create_patches(self): ...

    def apply_patches(self): ...

    def validate(self): ...


class DynaconfCore:
    def __init__(self, id: str):
        self.id = id
        self.env_data: dict[str, EnvState] = {
            "default": EnvState("default"),
            "_internal": EnvState("_internal"),
        }

    def get_envs(self, name=None) -> Iterable[EnvState]:
        return self.env_data.values()
