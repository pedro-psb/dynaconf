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
        # ensure all containres are DataDict/Lists
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = DataDict(value)
            elif isinstance(value, list):
                self[key] = DataList(value)

    def __setitem__(self, k, v):
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
        # ensure all containres are DataDict/Lists
        for key, value in enumerate(self):
            if isinstance(value, dict):
                self[key] = DataDict(value)
            elif isinstance(value, list):
                self[key] = DataList(value)


def metadata_get(obj: BaseData, k: str):
    metadata = getattr(obj, "__node_metadata__")
    return metadata[k]


def metadata_set(obj: BaseData, k: str, v):
    node_metadata = getattr(obj, "__node_metadata__")
    node_metadata[k] = v


def test_dynaconf_data_dict():
    import pytest
    from dynaconflib.core import DynaconfCore
    from dynaconflib.datastructures import SchemaTree

    data = DataDict()
    print(data)

    with pytest.raises(DynaconfNotInitialized, match="not initialized"):
        data.__get_dynaconf__()

    core = DynaconfCore("test", SchemaTree())
    data.__init_dynaconf__(core)
    assert core == data.__get_dynaconf__()
