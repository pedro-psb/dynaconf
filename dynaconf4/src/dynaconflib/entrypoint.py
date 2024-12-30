from __future__ import annotations

from typing import TypeVar
from .datastructures import LoadRequest, DataDict, SchemaTree, LoadDeclaration
from .core import DynaconfCore

T = TypeVar("T")


class DynaconfFront(DataDict):
    DYNACONF: DynaconfCore = None


def Dynaconf(schema: type[T] = DynaconfFront, *args, **kwargs) -> T:
    # parse init arguments
    instance_id = kwargs.get("name", "dynaconf")
    load_declaration_list: list[LoadDeclaration] = kwargs.get("load", [])
    data = kwargs.get("data", {})

    # initialize main data instance and dynaconf core
    settings = schema()
    schema_tree = SchemaTree.from_cls(schema)
    dynaconf_core = DynaconfCore(instance_id, schema_tree)

    # bind data and control
    settings.__dynaconf_core__ = dynaconf_core
    front_ns = dynaconf_core.namespaces.get("_frontend")
    front_ns.data = settings

    # load workflow
    init_load_request = LoadRequest("builtin.direct", "init", direct_data=data)
    dynaconf_core.enqueue_load_request(init_load_request)
    for load_declaration in load_declaration_list:
        for load_request in load_declaration:
            dynaconf_core.enqueue_load_request(load_request)
    dynaconf_core.load_pending()

    # preload_request are discovered dynamically and should be merged first
    for preload_request in dynaconf_core.get_preload_requests():
        dynaconf_core.enqueue_load_request(preload_request)
    dynaconf_core.load_pending(preload=True)

    # merge workflow
    dynaconf_core.merge_pending()
    dynaconf_core.validate("_frontend")

    # update _active data
    dynaconf_core.namespaces.update_frontend()
    return settings
