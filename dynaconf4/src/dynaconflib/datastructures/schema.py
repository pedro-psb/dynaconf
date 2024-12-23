from .tree import TreePath


class SchemaTree:
    def get_type(self, key: TreePath | str):
        return str

    @classmethod
    def parse(cls, schema: type):
        schema_tree = cls()
        return schema_tree


class SchemaNode:
    def __init__(self, key, value):
        self.key
        self.value = []
