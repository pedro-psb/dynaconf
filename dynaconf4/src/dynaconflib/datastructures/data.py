from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dynaconflib.core import DynaconfCore


class BaseDynaconfData:
    def __init__(self, *args, **kwargs):
        self.__dynaconf_core__ = None
        self.__node_metadata__ = {}
        super().__init__(*args, **kwargs)

    def __init_dynaconf__(self, dynaconf_core: DynaconfCore):
        self.__dynaconf_core__ = dynaconf_core

    def __get_dynaconf__(self):
        dynaconf_core = getattr(self, "__dynaconf_core__", None)
        if not dynaconf_core:
            raise RuntimeError("Dynaconf not initialized.")
        return dynaconf_core


class DataDict(dict, BaseDynaconfData): ...


class DataList(list, BaseDynaconfData): ...


def test_dynaconf_data_dict():
    import pytest
    from dynaconflib.core import DynaconfCore

    data = DataDict()
    print(data)

    with pytest.raises(RuntimeError, match="not initialized"):
        data.__get_dynaconf__()

    core = DynaconfCore("test")
    data.__init_dynaconf__(core)
    assert core == data.__get_dynaconf__()
