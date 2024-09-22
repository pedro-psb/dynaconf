from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .data_structs import BaseOptions
from .environment import EnvOptions
from .loading import LoadingOptions
from .merging import MergingOptions
from .validation import ValidationOptions


@dataclass
class StartupOptions(BaseOptions):
    """Settings that customize the behavior of the dynaconf initialization."""

    immediate_validation: bool = False


@dataclass
class SharedOptions(BaseOptions):
    """Settings that should be available in every module scope."""

    instance_name: str = "dynaconf"
    default_env_name: str = "default"


@dataclass
class InternalOptions(BaseOptions):
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


Options = InternalOptions  # alias

# Rudimentary "pre-sets"


def default_options() -> Options:
    return Options()


def strict_options(env_list: Optional[list[str]] = None) -> Options:
    strict_env_list = env_list or ["dev", "ci", "stage" "prod"]
    options = Options()
    options.validation.allow_non_schema_settings = False
    options.env.strict_env_list = strict_env_list
    return options


if __name__ == "__main__":
    import rich

    options = default_options()
    options.print()
