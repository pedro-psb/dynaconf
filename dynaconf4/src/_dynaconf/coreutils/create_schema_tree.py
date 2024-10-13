from _dynaconf.datastructures import DataDict, SchemaTree


def create_schema_tree(schema: type[DataDict]) -> SchemaTree:
    """Parse all types annotation in user-provided schema classes."""
    raise NotImplementedError()
