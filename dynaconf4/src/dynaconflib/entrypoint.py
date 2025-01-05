from __future__ import annotations

from typing import TypeVar
from .datastructures import LoadRequest, DataDict, SchemaTree, LoadDeclaration
from .core import DynaconfCore
from dynaconflib.public import FileLoader
from dynaconflib.utils import ensure_list

# from dynaconflib.public import LegacyParser
from contextlib import contextmanager

T = TypeVar("T")


class DynaconfApi:
    def __init__(self, core: DynaconfCore):
        self.__core__ = core

    def set(self, key, value): ...
    def get(self, key, fresh: bool = False, namespace: str = None): ...
    def freeze(self): ...
    @contextmanager
    def namespace_context(self, namespace: str): ...


class BaseSchema(DataDict):
    def __init__(self, dynaconf_api: DynaconfApi, *args, **kwargs):
        self.DYNACONF = dynaconf_api
        super().__init__(*args, **kwargs)


def Dynaconf(schema: type[T] = BaseSchema, *args, **kwargs) -> T:
    special_kwargs = ("setting_files", "environments", "instance_id")

    # parse init arguments
    instance_id = kwargs.get("name", "dynaconf")
    setting_files = ensure_list(kwargs.get("setting_files", []))
    data = {k: v for k, v in kwargs.items() if k.lower() not in special_kwargs}

    # initialize main data instance and dynaconf core
    schema_tree = SchemaTree.from_cls(schema)
    dynaconf_core = DynaconfCore(instance_id, schema_tree)
    dynaconf_api = DynaconfApi(dynaconf_core)
    settings = schema(dynaconf_api)

    # bind data and control
    settings.__init_dynaconf__(dynaconf_core)
    front_ns = dynaconf_core.namespaces.get("_frontend")
    front_ns.data = settings

    # load workflow
    load_request_direct = LoadRequest("builtin.direct", "init", direct_data=data)
    load_request_files = FileLoader(setting_files).build() if setting_files else []
    load_request_environ = LoadRequest("builtin.environ", "init")
    load_request_list = [load_request_direct, *load_request_files, load_request_environ]
    for load_request in load_request_list:
        dynaconf_core.enqueue(load_request=load_request)
    dynaconf_core.process_api(load=all)

    # preload_request are discovered dynamically and should be merged first
    for preload_request in dynaconf_core.get_preload_requests():
        dynaconf_core.enqueue(load_request=preload_request)
    dynaconf_core.process_api(load=all)

    # merge workflow
    dynaconf_core.process_api(merge=all)
    dynaconf_core.validate("_frontend")
    return settings
