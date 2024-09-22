from ..data_structs import DataDict, DynaconfToken, SchemaTree, DynaconfTree


class DefaultDynaconfParser:
    PARSER_ID = "default"

    def parse_tree(self, data: dict, schema_tree: SchemaTree) -> DynaconfTree:
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
          on the key access.
        """
        raise NotImplementedError()  # TODO: implement

    def _handle_dynaconf_string(self, dynaconf_string: str) -> DynaconfToken:
        raise NotImplementedError()  # TODO: implement
