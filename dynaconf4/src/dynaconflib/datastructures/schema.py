from __future__ import annotations
from typing import NamedTuple
from dynaconflib.utils import SENTINEL
from dynaconflib.exceptions import SchemaError


class SchemaNode(NamedTuple):
    key: str | int | Index
    key_type: type
    value_type: type
    children_key_type: type

    def __eq__(self, o):
        return all([getattr(o, f) == getattr(self, f) for f in self._fields])


class Index(int):
    def __eq__(self, o):
        return type(self) is type(o)

    def __hash__(self):
        return hash(Index)


class SchemaTree:
    def __init__(self, strict: bool = False):
        self.type_map = {}
        self.root = SchemaNode("root", str, dict, str)
        self.defaults_map = {}
        self.strict = strict

    @classmethod
    def from_cls(cls, schema_cls: type) -> SchemaTree:
        # TODO: actually parse the type info into SchemaNodes
        return SchemaTree()

    def add(self, key_path, value_type, children_key_type=str, default=None):
        """
        Add a value_type to a schema node in the given location.

        Params:
            key_path: The location of the schema node.
            value_type: The type of this node.
            children_key_type: The type of the node children, if dict or list.
        """
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

    def get(self, key_path, raises=True) -> SchemaNode:
        try:
            return self.type_map[tuple(key_path)]
        except KeyError as e:
            if raises is False:
                return None
            raise SchemaError(
                f"Failed to find node in path={str(e)}. Strict-mode={self.strict}."
            )

    def get_path(self, *, from_raw: tuple[str]) -> list[SchemaNode]:
        if self.strict:
            return self._create_schema_path(from_raw)
        else:
            return self._create_default_schema_path(from_raw)

    def compute_default_schema(self, root_data: dict, path=None):
        """Compute default schema for non-strict schema mode.

        When strict-mode is False, data can contain unknown node types. Either a schema was
        provided for some nodes but data contains extra nodes or no schema was provided.
        In this case, we use existing data structure to create a schema_map.

        Params:
            root_data: The source of truth for the types.
            path: The path to a sub-node where the computing will being. Default=(,) (root).
        """

    def _create_schema_path(self, from_raw: tuple[str]) -> list[SchemaNode]:
        final = []
        raw_path = tuple(from_raw)
        parent_node = self.root
        for i in range(len(raw_path)):
            # take each sub patch from start to i
            cur_path = raw_path[: i + 1]
            key = cur_path[-1]
            # handle case where parent is list
            if parent_node.value_type is list:
                key = Index(int(key))
                cur_path = cur_path[:i] + (key,)
                raw_path = cur_path + raw_path[i + 1 :]
            # add to transformed list
            current_node = self.get(tuple(cur_path))._replace(key=key)
            final.append(current_node)
            # update
            parent_node = current_node
        return final

    def _create_default_schema_path(self, raw_path: tuple[str]) -> list[SchemaNode]:
        final: list[SchemaNode] = []
        raw_path = tuple(raw_path)
        for i, node in enumerate(raw_path):
            is_list_item = is_digit(node)
            if is_list_item:
                if i == 0:
                    raise ValueError("First item's key can't be an integer")
                final[-1] = final[-1]._replace(
                    key_type=str, value_type=list, children_key_type=int
                )
                new_node = SchemaNode(int(node), int, dict, children_key_type=str)
            else:
                new_node = SchemaNode(node, str, dict, children_key_type=str)
            final.append(new_node)
        return final

    def __repr__(self):
        return f"{self.__class__.__name__}({self.type_map!r})"

    def __str__(self):
        return str(self.type_map)


def is_digit(value: int | str) -> bool:
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        return True
    return False
