from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
from _dynaconf.abstract import BaseOptions

if TYPE_CHECKING:
    from .dynaconf_options import SharedOptions


@dataclass
class ValidationOptions(BaseOptions):
    allow_non_schema_settings: bool = False


class ValidationManager:
    def __init__(
        self, shared_options: SharedOptions, options: Optional[ValidationOptions]
    ):
        opts = options or ValidationOptions
        self.options = opts
        self.shared_options = shared_options
