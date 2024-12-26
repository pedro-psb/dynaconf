from typing import NamedTuple


class SchemaNode(NamedTuple):
    key: str | int
    key_type: type
    value_type: type
    children_key_type: type

    def __eq__(self, o):
        return all([getattr(o, f) == getattr(self, f) for f in self._fields])


class Index(NamedTuple):
    value: int = 0

    def __eq__(self, o):
        return type(self) is type(o)

    def __hash__(self):
        return hash(Index)


class SchemaTree:
    def __init__(self):
        self.type_map = {}
        self.root = SchemaNode("root", str, dict, str)

    def add(self, key_path, value_type, children_key_type=str):
        # TODO make sanity checks.
        # E.g:
        # 1. [(A, k=str, v=list), (B, k=str, v=int)] is invalid, because
        #    Node A is a list and its child B has k=str (must be INDEX)
        # 2. [(A, v=int), (B, v=bool)] is invalid, because Node A has
        #    children, but it is has value=int
        key = key_path[-1]
        key_type = int if isinstance(key, Index) else type(key)
        if value_type not in (dict, list):
            children_key_type = None
        elif value_type is list:
            children_key_type = int
        self.type_map[tuple(key_path)] = SchemaNode(
            key, key_type, value_type, children_key_type
        )

    def get(self, key_path) -> SchemaNode:
        return self.type_map[tuple(key_path)]

    def raw_to_schema_path(self, raw_path: list[str]) -> list[SchemaNode]:
        final = []
        parent_node = self.root
        for i in range(len(raw_path)):
            # take each sub patch from start to i
            cur_path = raw_path[: i + 1]
            key = cur_path[-1]
            # handle case where parent is list
            if parent_node.value_type is list:
                key = Index(int(key))
                cur_path = cur_path[:i] + [key]
                raw_path = cur_path + raw_path[i + 1 :]
            # add to transformed list
            current_node = self.get(tuple(cur_path))._replace(key=key)
            final.append(current_node)
            # update
            parent_node = current_node
        return final

    def __str__(self):
        return str(self.type_map)
