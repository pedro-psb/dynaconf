from pathlib import Path
from typing import Optional

from _dynaconf.config import DynaconfConfig
from _dynaconf.datastructures import LoadContext, LoadRequest


def legacy_config_adapter(legacy_options: dict) -> dict:
    """Transform instance configs from dynaconf3 to dynaconf4 config names/structure."""
    raise NotImplementedError()


class ControlLayer:
    def __init__(self, instance_id):
        # The value that identifies this dynaconf instance
        # Used for envvar prefix
        self.instance_id = instance_id

    def load(self, load_request): ...

    def add_load_request(self, *load_request: LoadRequest): ...

    def flush_load(self): ...
    def flush_merge(self): ...
    def flush_validate(self): ...


PathLike = str | Path


class Dynaconf:
    def __self__(
        self,
        settings_files: Optional[PathLike | list[PathLike]] = None,
        environments: Optional[bool] = None,
        envvar_prefix: Optional[str] = None,
    ):
        instance_config = {
            "settings_files": settings_files,
            "environments": environments,
        }

        # Control Layer stuff

        instance_id = envvar_prefix or "dynaconf"
        control = ControlLayer(instance_id)

        # TODO: load dynaconf settings like we usually do
        # but move that to an internal namespace which only exist
        # on a internal environment
        control.add_load_request(
            LoadRequest(
                loader_id="direct",
                uri="",
                direct_data=instance_config,
            ),
            LoadRequest(
                loader_id="os_environ",
                uri="",
                keys=["dynaconf_config"],
            ),
        )
        control.flush_load()
        control.flush_merge()
        control.flush_validate()
