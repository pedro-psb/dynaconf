from __future__ import annotations

from typing import TypeVar, Optional
from .registry import RegistryManager, BaseRegistry
from .datastructures import MergeResult
from .core import DynaconfCore

T = TypeVar("T")


def Dynaconf(schema: type[T], *args, **kwargs) -> T:
    # parse init arguments
    instance_id = kwargs.get("name", "dynaconf")
    loaders = kwargs.get("loaders", [])
    data = kwargs.get("data", {})

    # initialize main data instance and dynaconf core
    instance = schema()
    dynaconf_core = DynaconfCore(instance_id)

    # bind data and control
    instance.__dynaconf_core__ = dynaconf_core
    dynaconf_core.namespace_data.add("default", instance)

    # run loaders
    dynaconf_core.load(loader_id="direct", payload={"data": data})
    for loader in loaders:
        dynaconf_core.load(loader_id=loader.id, payload=loader.payload)

    for preloader in dynaconf_core.pending_merge.get_dynamic_preloads():
        dynaconf_core.load(preloader.id, payload=preloader.payload)

    dynaconf_core.merge_pending_data(env="default")
    dynaconf_core.validate("default")

    return instance
