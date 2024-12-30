from __future__ import annotations
from typing import TYPE_CHECKING
from dynaconflib.exceptions import DynaconfNotInitialized
from .load import LoadRequest
from contextlib import contextmanager

if TYPE_CHECKING:
    from dynaconflib.core import DynaconfCore


class BaseDynaconfData:
    def __init__(self, *args, **kwargs):
        self.__dynaconf_core__ = None
        super().__init__(*args, **kwargs)

    def __init_dynaconf__(self, dynaconf_core: DynaconfCore):
        self.__dynaconf_core__ = dynaconf_core

    def __get_dynaconf__(self, raises=True):
        dynaconf_core = getattr(self, "__dynaconf_core__", None)
        if not dynaconf_core and raises is True:
            raise DynaconfNotInitialized("Dynaconf not initialized.")
        return dynaconf_core

    @contextmanager
    def __dynaconf_setmode__(self):
        metadata_set(self, "internal_setmode", True)
        try:
            yield
        finally:
            metadata_set(self, "internal_setmode", False)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__dict__})"


class DataDict(dict, BaseDynaconfData):
    def __init__(self, *args, **kwargs):
        self.__node_metadata__ = {"path": None, "internal_setmode": False}
        super().__init__(*args, **kwargs)

    def __setitem__(self, k, v):
        # If dynaconf is not initizalied, it behaves as a normal dict
        try:
            core = self.__get_dynaconf__()
        except DynaconfNotInitialized:
            key = getattr(k, "key", k)
            super().__setitem__(key, v)
            return

        # 'setmode' marks a state where we can directly set on the DataDict
        #
        # * Direct setting should only happen internally on the patch process.
        #   This ensures there is a single setpoint where ALL data passes, so
        #   we can safely record inspect data and have a consistent set workflow.
        # * When called from another context (e.g the user calls it), it is not in
        #   setmode, so it trigger a load/patch workflow, that is then able to save
        #   the data in the DataDict|DataList
        # * TODO: to ensure that, all nested dict/list should be DataDict and DataList
        setmode = metadata_get(self, "internal_setmode")
        if setmode:
            super().__setitem__(k, v)
        else:
            load_request = LoadRequest(
                "builtin.direct", "__setattr__", direct_data={k: v}
            )
            core.enqueue_load_request(load_request)
            core.load_pending()
            current_ns = core.namespaces.get()
            with self.__dynaconf_setmode__():
                current_ns.process_loaded(core.patch_engine)
                current_ns.process_patches(core.patch_engine)
                core.update_frontend()

    def __repr__(self):
        instance_id = None
        if core := self.__get_dynaconf__(raises=False):
            instance_id = core.id
        return f"{self.__class__.__name__}(id={instance_id!r}, {dict(self)!r})"


def metadata_get(obj: BaseDynaconfData, k: str):
    metadata = getattr(obj, "__node_metadata__")
    return metadata[k]


def metadata_set(obj: BaseDynaconfData, k: str, v):
    node_metadata = getattr(obj, "__node_metadata__")
    node_metadata[k] = v


class DataList(list, BaseDynaconfData): ...


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

    # assert setmode
    assert metadata_get(data, "internal_setmode") is False
    with data.__dynaconf_setmode__():
        assert metadata_get(data, "internal_setmode") is True
    assert metadata_get(data, "internal_setmode") is False
