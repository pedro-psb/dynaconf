from ..data_structs import SchemaTree
from _dynaconf.datastructures import DynaconfToken
from _dynaconf.abstract import BaseMergeTree

class DefaultEvaluator:
    PARSER_ID = "default"

    def parse_tree(self, data: dict, schema_tree: SchemaTree) -> BaseMergeTree:
        """Parse raw python data into dynaconf specific data-structures.

        The main structures are is the dynaconf tree (made of DataDict and DataList), which
        should contain internal private data. Some relevant private data include:
        * merge strategy or operations for each node. This requires proper merge priority resolution,
          from the global strategy to the local override, if there is one.
        * dynaconf-lang tokens for lazy evaluations. Early evaluations also needs tokenization,
          but its transformation should be performed immediately.

        Some converters that requires lazy evaluation are:
        * Values that depends on other values (variable interpolation).
        * Transformation function that needs to be triggered some time after loading, for example,
          on key access.

        Params:
            data: The python dict/list tree with potential to be parsed.
            schema_tree: The user-defined schema-tree providing context on some parsing decisions.
        """
        raise NotImplementedError()  # TODO: implement

    def _tokenize_dynaconf_string(self, dynaconf_string: str) -> DynaconfToken:
        raise NotImplementedError()  # TODO: implement

    def evaluate_lazy_settigns(self, merge_tree: BaseMergeTree, context: dict):
        """Evaluate lazy values in a DynaconfTree structure.

        Params:
            dynaconf_tree: The tree which should have it's lazy values evaluated. The final values ARE NOT special objects.
            context: The context used for variable interpolation lookup.
        """
        raise NotImplementedError()  # TODO: implement
