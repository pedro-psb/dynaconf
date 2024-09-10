from __future__ import annotations

from typing import Optional

from .core import DynaconfCore
from .data_structs import SchemaTree
from .dynaconf_options import Options
from .typed.type_definitions import DataDict

SchemaType = type[DataDict]  # actually a subclass of that


def parse_schema(schema: SchemaType) -> SchemaTree:
    return SchemaTree()


def Dynaconf(
    schema: SchemaType, *args, options: Optional[Options] = None, **kwargs
) -> tuple[DataDict, DynaconfApi]:
    """Dynaconf builder/initializer."""
    # internal layer
    schema_tree = parse_schema(schema)
    final_options = options or Options()
    dynaconf_core = DynaconfCore(schema_tree, final_options)

    # user-facing layer
    settings = schema()
    dynaconf = DynaconfApi(dynaconf_core)
    return settings, dynaconf


class DynaconfApi:
    def __init__(self, dynaconf_core: DynaconfCore):
        self.load = LoadApi()
        self.validation = ValidationApi()
        self.env = EnvApi()
        self.__dynaconf_core__ = dynaconf_core

    def simple_load(
        self,
        settings: Optional[str | list[str]] = None,
        *,
        immediate: bool = True,
        loadenv_last: bool = True,
    ): ...


class DynaconfLegacyApi:
    def __init__(self, dynaconf_core: DynaconfCore):
        self.__dynaconf_core__ = dynaconf_core

    def get_fresh(self, key, fresh=False): ...

    def exists(self, key, fresh=False): ...

    def as_dict(self): ...


class LoadApi:
    def add(self): ...

    def run(self): ...

    def get(self): ...

    def list(self): ...


class ValidationApi:
    def add(self): ...

    def run(self): ...

    def list(self): ...


class EnvApi:
    def context(self): ...

    def get(self): ...

    def list(self): ...
