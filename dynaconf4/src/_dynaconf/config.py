from __future__ import annotations

from dataclasses import dataclass, field

from _dynaconf.control.environment import EnvOptions
from _dynaconf.control.loading import LoadingOptions
from _dynaconf.control.merging import MergingOptions
from _dynaconf.control.validation import ValidationOptions
from _dynaconf.abstract import BaseOptions
import rich


@dataclass
class Options(BaseOptions):
    def print(self):
        rich.print(self)


@dataclass
class StartupOptions(Options):
    """Settings that customize the behavior of the dynaconf initialization."""

    immediate_validation: bool = False


@dataclass
class SharedOptions(Options):
    """Settings that should be available in every module scope."""

    instance_name: str = "dynaconf"
    default_env_name: str = "default"


@dataclass
class InternalOptions(Options):
    # General options
    shared: SharedOptions = field(default_factory=SharedOptions)
    startup: StartupOptions = field(default_factory=StartupOptions)

    # Module options
    loading: LoadingOptions = field(default_factory=LoadingOptions)
    merging: MergingOptions = field(default_factory=MergingOptions)
    validation: ValidationOptions = field(default_factory=ValidationOptions)
    env: EnvOptions = field(default_factory=EnvOptions)

    def print(self):
        rich.print(self)
