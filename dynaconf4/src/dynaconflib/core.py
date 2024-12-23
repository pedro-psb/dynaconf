from typing import Iterable
from dynaconflib.datastructures import DataDict, LoadRequest, BasePatch
from dynaconflib.registry import LoaderRegistry, TokenRegistry, PatchOpRegistry, ValidatorRegistry


class EnvState:
    # shared registries
    loaders_reg = LoaderRegistry("loaders")
    token_callbacks_reg = TokenRegistry("token_callbacks")
    merge_operations_reg = PatchOpRegistry("merge_operations")
    validator_reg = ValidatorRegistry("validators")

    def __init__(self, name):
        self.name = name
        self.data = None
        self.pending_load_request: list[LoadRequest] = []
        self.pending_patch_create: list[DataDict] = []
        self.pending_patch_apply: list[BasePatch] = []

    def load_pending(self): ...

    def create_patches(self): ...

    def apply_patches(self): ...

    def validate(self): ...


class DynaconfCore:
    def __init__(self, id: str):
        self.id = id
        self.namespace_data: dict[str, EnvState] = {
            "default": EnvState("default"),
            "_internal": EnvState("_internal"),
        }

    def get_envs(self, name=None) -> Iterable[EnvState]:
        return self.namespace_data.values()
