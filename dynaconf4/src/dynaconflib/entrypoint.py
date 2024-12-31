from __future__ import annotations

from typing import TypeVar
from .datastructures import LoadRequest, DataDict, SchemaTree, LoadDeclaration
from .core import DynaconfCore
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
    # parse init arguments
    instance_id = kwargs.get("name", "dynaconf")
    load_declaration_list: list[LoadDeclaration] = kwargs.get("load", [])
    data = kwargs.get("data", {})

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
    load_request_environ = LoadRequest("builtin.environ", "init")

    dynaconf_core.enqueue(load_request=load_request_direct)
    for load_declaration in load_declaration_list:
        for load_request in load_declaration:
            dynaconf_core.enqueue(load_request=load_request)
    dynaconf_core.enqueue(load_request=load_request_environ)
    dynaconf_core.process_api(load=all)

    # preload_request are discovered dynamically and should be merged first
    for preload_request in dynaconf_core.get_preload_requests():
        dynaconf_core.enqueue(load_request=preload_request)
    dynaconf_core.process_api(load=all)

    # merge workflow
    dynaconf_core.process_api(merge=all)
    dynaconf_core.validate("_frontend")
    return settings
