from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .data_structs import SchemaTree, DynaconfTree
from .builtin.dynaconf_parser import DefaultDynaconfParser
from dataclasses import dataclass

if TYPE_CHECKING:
    from .dynaconf_options import SharedOptions


@dataclass
class EvaluationOptions: ...


class EvaluationManager:
    """Reponsible for creating and manipulating DynaconfTrees."""

    def __init__(
        self,
        shared_options: SharedOptions,
        options: Optional[EvaluationOptions] = None,
    ):
        self.shared_options = shared_options
        self.options = options or EvaluationOptions()

        self.dynaconf_parser = DefaultDynaconfParser()

    def replace_parser(self, parser_instance: DefaultDynaconfParser):
        # TODO: validate it subclasses the BaseDynaconfParsing
        self.dynaconf_parser = parser_instance

    def parse_tree(self, data: dict, schema_tree: SchemaTree) -> DynaconfTree:
        """Parse a raw dict into a dynaconf tree, composed of DataDict and DataList.

        These objects contains private internal data to support merging strategies, lazy
        evaluation and validation.
        """
        return self.dynaconf_parser.parse_tree(data, schema_tree)

    def evalute_lazy_values(self, dynaconf_tree: DynaconfTree):
        """Evaluate lazy values from tree, if there are any."""
        raise NotImplementedError()  # TODO: implement
