from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from .data_structs import DynaconfTree

if TYPE_CHECKING:
    from .dynaconf_options import SharedOptions


@dataclass
class MergingOptions:
    global_dict_merge: bool = False


class MergingManager:
    def __init__(
        self, shared_options: SharedOptions, options: Optional[MergingOptions] = None
    ):
        opts = options or MergingOptions()
        self.merging_ops_registry = None  # TOOD: structure how these will work
        self.options = opts
        self.shared_options = opts

    def merge_data(self, base_data: DynaconfTree, income_data: DynaconfTree) -> None:
        """Merges income_data into base_data in-place (mutates)."""
        raise NotImplementedError()
