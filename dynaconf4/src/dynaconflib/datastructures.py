from dataclasses import dataclass


@dataclass
class MergeResult: ...


class DataPatch: ...


class LoadRequest: ...


class DataDict(dict):
    def __init__(self, *args, **kwargs):
        self.__dynaconf_core__ = None
        self.__node_metadata__ = {}
        super().__init__(*args, **kwargs)

    def __init_dynaconf__(self, id: str):
        self.__dynaconf_core__ = DynaconfCore(id)

    def __get_dynaconf__(self):
        dynaconf_core = self.__dynaconf_core__
        if not dynaconf_core:
            raise RuntimeError("Dynaconf not initialized.")
        return dynaconf_core


class DataList(list):
    def __init__(self, *args, **kwargs):
        self.__dynaconf_core__ = None
        self.__node_metadata__ = {}
        super().__init__(*args, **kwargs)

    def __init_dynaconf__(self, id: str):
        self.__dynaconf_core__ = DynaconfCore(id)

    def __get_dynaconf__(self):
        dynaconf_core = self.__dynaconf_core__
        if not dynaconf_core:
            raise RuntimeError("Dynaconf not initialized.")
        return dynaconf_core
