from .data_structs import DataDict, SchemaTree


def parse_schema(schema: type[DataDict]) -> SchemaTree:
    """Parse all types annotation in user-provided schema classes."""
    return SchemaTree()


class Settings(DataDict):
    database: str
    port: int
