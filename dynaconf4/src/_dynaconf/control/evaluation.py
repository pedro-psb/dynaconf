from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Callable

from _dynaconf.datastructures import SchemaTree
from _dynaconf.abstract import BaseMergeTree
from dataclasses import dataclass

if TYPE_CHECKING:
    from .dynaconf_options import SharedOptions

# alias for semantic typing
TokenId = str
Transformer = Callable  # TODO: define transformer API more clearly


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

        self.token_transformer_registry: dict[TokenId, Transformer] = {}
        self.evaluator = DefaultEvaluator()

    def add_transformer(self, token_id: str, callback: Transformer):
        if token_id in self.token_transformer_registry:
            raise ValueError(f"Converter already registered: {token_id}")
        self.token_transformer_registry[token_id] = callback

    def replace_evaluator(self, evaluator_instance: DefaultEvaluator):
        # TODO: validate that it subclasses the BaseEvalutor
        self.evaluator = evaluator_instance

    def parse_tree(self, data: dict, schema_tree: SchemaTree) -> BaseMergeTree:
        """Parse a raw dict into a dynaconf tree, composed of DataDict and DataList.

        These objects contains private internal data to support merging strategies, lazy
        evaluation and validation.
        """
        return self.evaluator.parse_tree(data, schema_tree)

    def evalute_lazy_values(self, dynaconf_tree: BaseMergeTree, context: dict):
        """Evaluate lazy values from tree, if there are any."""
        self.evaluator.evaluate_lazy_settigns(dynaconf_tree, context)
