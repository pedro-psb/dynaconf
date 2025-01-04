from __future__ import annotations
from typing import TYPE_CHECKING
from dynaconflib.exceptions import DynaconfNotInitialized
from collections import defaultdict

if TYPE_CHECKING:
    from dynaconflib.core import DynaconfCore


class BaseData:
    def __init_dynaconf__(self, dynaconf_core: DynaconfCore):
        self.__node_metadata__["core"] = dynaconf_core

    def __get_dynaconf__(self, raises=True):
        dynaconf_core = self.__node_metadata__["core"]
        if not dynaconf_core and raises is True:
            raise DynaconfNotInitialized("Dynaconf not initialized.")
        return dynaconf_core


class DataDict(dict, BaseData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # dont know why I cant move metadata init to the BaseData init
        self.__node_metadata__ = {
            "path": None,
            "core": None,
            "id": id(self) % 100,
            "namespace": None,
            "patched_keys": defaultdict(list),
        }
        convert_containers(self, self.items())

    def update(self, data):
        super().update(ensure_containers(data))

    def copy(self):
        return self.__class__(super().copy())

    def setdefault(self, k, v):
        return super().setdefault(k, ensure_containers(v))

    def __setitem__(self, k, v):
        initialized = core = self.__get_dynaconf__(raises=False)
        if not initialized or core.is_merging():
            super().__setitem__(k, ensure_containers(v))
        else:  # caled from user
            core.direct_ingest("__setattr__", path=(k,), value=v)

    def __repr__(self):
        return f"{self.__class__.__name__}({dict(self)!r})"


class DataList(list, BaseData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__node_metadata__ = {
            "path": None,
            "core": None,
            "patched_keys": defaultdict(list),
        }
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

    def __repr__(self):
        return f"{self.__class__.__name__}({list(self)!r})"


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
