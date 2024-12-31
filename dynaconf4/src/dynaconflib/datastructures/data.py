from __future__ import annotations
from typing import TYPE_CHECKING
from dynaconflib.exceptions import DynaconfNotInitialized
from .load import LoadRequest

if TYPE_CHECKING:
    from dynaconflib.core import DynaconfCore


class BaseData:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__node_metadata__ = {"path": None}
        self.__convert_nested__()

    def __init_dynaconf__(self, dynaconf_core: DynaconfCore):
        self.__dynaconf_core__ = dynaconf_core

    def __get_dynaconf__(self, raises=True):
        dynaconf_core = getattr(self, "__dynaconf_core__", None)
        if not dynaconf_core and raises is True:
            raise DynaconfNotInitialized("Dynaconf not initialized.")
        return dynaconf_core

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


class DataDict(dict, BaseData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        convert_containers(self, self.items())

    def update(self, data):
        super().update(ensure_containers(data))

    def copy(self):
        return self.__class__(super().copy())

    def setdefault(self, k, v):
        return super().setdefault(k, ensure_containers(v))

    def __setitem__(self, k, v):
        v = ensure_containers(v)

        # If dynaconf is not initizalied, it behaves as a normal dict
        if not (core := self.__get_dynaconf__(raises=False)):
            super().__setitem__(k, v)
            return

        # Internal vs User __setattr__ calls:
        # * Set calls from user must pass through the ingestion pipeline
        # * Set calls from core (internal) are set normally
        called_from_core = core.status == core.STATUS_SET.MERGING
        called_from_user = not called_from_core
        if called_from_core:
            super().__setitem__(k, v)
        elif called_from_user:
            load_request = LoadRequest(
                "builtin.direct", "__setattr__", direct_data={k: v}
            )
            core.enqueue(load_request=load_request)
            core.process_api(load=all, merge=all)

    def __repr__(self):
        instance_id = None
        if core := self.__get_dynaconf__(raises=False):
            instance_id = core.id
        return f"{self.__class__.__name__}(id={id(self)%1000}, core={instance_id!r}, {dict(self)!r})"


class DataList(list, BaseData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        convert_containers(self, enumerate(self))

    def copy(self):
        return self.__class__(super().copy())

    def append(self, v):
        super().append(ensure_containers(v))

    def insert(self, i, v):
        super().insert(i, ensure_containers(v))

    def extend(self, data):
        super().extend(ensure_containers(data))

    def __setitem__(self, k, v):
        super().__setitem__(k, ensure_containers(v))

    def __add__(self, v):
        super().__add__(ensure_containers(v))

    def __iadd__(self, v):
        return super().__iadd__(ensure_containers(v))


def convert_containers(data, iter):
    for key, value in iter:
        if isinstance(value, dict):
            data[key] = DataDict(value)
        elif isinstance(value, list):
            data[key] = DataList(value)


def ensure_containers(data):
    if data.__class__ is dict:
        return DataDict(data)
    elif data.__class__ is list:
        return DataList(data)
    return data


def metadata_get(obj: BaseData, k: str):
    metadata = getattr(obj, "__node_metadata__")
    return metadata[k]


def metadata_set(obj: BaseData, k: str, v):
    node_metadata = getattr(obj, "__node_metadata__")
    node_metadata[k] = v
