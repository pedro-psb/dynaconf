from __future__ import annotations
from typing import NamedTuple, Sequence, Optional, Callable, TypeVar, Generic
from _dynaconf.abstract import BaseOperation, BaseMergeTree, BaseSchemaTree
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _dynaconf.token_registry import Merge

TokenName = str
EnvName = str
T = TypeVar("T")


def is_token(value: str) -> bool:
    if not isinstance(value, str):
        return False
    return isinstance(value, str) and value.startswith("@")


def ensure_path(path: TreePath | str) -> TreePath:
    def cast_int(s):
        try:
            return int(s)
        except ValueError:
            return s

    if isinstance(path, str):
        return TreePath([cast_int(val) for val in path.split(".")])
    return path


def ensure_rooted(_data: dict):
    if "root" not in _data.keys():
        return {"root": _data}
    return _data


# dynaconf data objects


class DataDict(dict):
    def __init__(self, *args, **kwargs):
        self.__dynaconf_data = {
            "validators": None,
            "lazy_tokens": [],
        }
        super().__init__(*args, **kwargs)

    def __init_dynaconf__(self, dynaconf_api):
        self.__dynaconf_data__["dynaconf_api"] = dynaconf_api

    def get_dynaconf(self):
        dynaconf_api = self.__dynaconf_data__.get("dynaconf_api", None)
        if not dynaconf_api:
            raise RuntimeError("Dynaconf not initialized.")
        return dynaconf_api


class DataList(list): ...


# loader related


class Loader(NamedTuple):
    read: Callable
    parse: Callable
    split_envs: Callable


class LoadContext(NamedTuple):
    default_env_name: str = None
    envvar_prefix: str = None
    allowed_envs: list[str] = None
    schema_tree: BaseSchemaTree = None
    only_schema_keys: bool = True


class LoadRequest(NamedTuple):
    loader_id: str
    uri: str
    order: int = 0
    has_explicit_envs: Optional[bool] = None
    allowed_env_list: Optional[list] = None
    direct_data: Optional[dict] = None


class SchemaTree(BaseSchemaTree):
    def get_key_type(self, key):
        return str


# linear data structures


class LinearDataStructure(Generic[T]):
    def __init__(self):
        self._data = []

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def __repr__(self):
        return repr(self._data)


class Stack(LinearDataStructure[T]):
    def pop(self) -> T:
        return self._data.pop()

    def push(self, item: T):
        self._data.append(item)

    def reverse(self):
        self._data.reverse()


class Queue(LinearDataStructure):
    def dequeue(self):
        return self._data.pop(0)

    def enqueue(self, item):
        self._data.insert(0, item)


# trees related


class TreePath(tuple):
    def as_str(self):
        return ".".join(self)

    def __add__(self, x: Sequence | str | int):
        if isinstance(x, list | tuple):
            return TreePath(tuple(self) + tuple(x))
        elif isinstance(x, str | int):
            return TreePath(tuple(self) + (x,))
        else:
            TypeError("Type not supported.")

    def __repr__(self):
        return f"{self.__class__.__name__}{super().__repr__()}"


class PartialToken(NamedTuple):
    id: str
    args: Optional[str]


class DynaconfToken(NamedTuple):
    id: str
    args: Optional[str]
    is_lazy: bool
    fn: Callable
    next: Optional[DynaconfToken]
    is_container_level: bool = False


class TokenCallback(NamedTuple):
    fn: Callable
    is_lazy: bool = False
    is_merge_operation: bool = False


class MergeTree(BaseMergeTree):
    def __init__(
        self,
        merge_op_map: Optional[dict[TreePath | str, list[BaseOperation]]] = None,
        meta_token_map: Optional[dict[TreePath | str, list[DynaconfToken]]] = None,
    ):
        _merge_op_map = (
            {ensure_path(k): v for k, v in merge_op_map.items()}
            if merge_op_map
            else None
        )
        _meta_token_map = (
            {ensure_path(k): v for k, v in meta_token_map.items()}
            if meta_token_map
            else None
        )
        self._merge_operation_data: dict[TreePath, list[BaseOperation]] = (
            _merge_op_map or {}
        )
        self._meta_token_data: dict[TreePath, list[DynaconfToken]] = (
            _meta_token_map or {}
        )

    def get(self, path: TreePath | str) -> list[BaseOperation] | None:
        return self._merge_operation_data.get(ensure_path(path), None)

    def add(self, path, value):
        self._merge_operation_data.setdefault(path, [])
        self._merge_operation_data[path].append(value)

    def add_meta_token(self, path, token):
        self._meta_token_data.setdefault(path, [])
        self._meta_token_data[path].append(token)

    def get_meta_token(self, path: TreePath | str, token_id: Optional[str] = None):
        """Get a meta token related to a path.

        Returns a tuple of DynaconfTokens at this path, or one DynaconfToken if token_id is given.
        """
        meta_tokens = self._meta_token_data.get(ensure_path(path), [])
        if token_id:
            query = [it for it in meta_tokens if it.id == token_id]
            return query[0] if query else None
        return tuple(meta_tokens) if meta_tokens else tuple()

    def __eq__(self, o):
        return (
            self._merge_operation_data == o._merge_operation_data
            and self._meta_token_data == o._meta_token_data
        )


class MergeTree2(BaseMergeTree):
    """Example of doing a different implementation.

    Implemeting all base class methods should make it work seamingless.
    """

    def __init__(self, root: Merge):
        self._tree = root

    def get(self, path: TreePath):
        def _get(p: tuple[str | int, ...]):
            if len(p) == 1:
                return self._tree.value["root"][p[-1]]
            return _get(p[:-1])[p[-1]]

        return _get(path)


class MergePolicyFactorWeightMap(NamedTuple):
    """The weights that will be used to determine what Rule win over the other.

    It may be hard for a human to determine the right weights for a desired behavior, due
    to the combinatorial possibilites of all conflicts. But it shouldn't be hard to
    use an algorithm to set the values while respecting some high-level behavior constraints,
    so that's the recommended approach for finding those values.

    Has the form: {factor}: tuple({weight-for-false}, {weight-for-true})
    """

    container_scoped: tuple[int, int] = (0, 0)
    propagates: tuple[int, int] = (0, 0)
    from_schema: tuple[int, int] = (0, 0)


class MergePolicyFactorComb(NamedTuple):
    """The MergePolicy factors combination that influences a Rule priority resolution.

    Params:
        container_scoped: If a Rule is scoped at the container level or at the item-level.
        propagates: If a Rule should propagate or not (a one-off).
        from_schema: If a Rule was defined in the schema (statically) or dynamically.
            Example, in a settings file with dynaconf tokens.
    """

    container_scoped: bool
    propagates: bool
    from_schema: bool

    def calculate_weight(self, factor_weight_map: MergePolicyFactorWeightMap) -> int:
        """The weight of this instance combinaction of factors.
        TODO: the weight can be cached for each instance.
        """
        # Index is 0 for False and 1 for True, because int(False) == 0, int(True) == 1
        container_scoped_w = factor_weight_map.container_scoped[
            int(self.container_scoped)
        ]
        propagates_w = factor_weight_map.propagates[int(self.propagates)]
        from_schema_w = factor_weight_map.from_schema[int(self.from_schema)]
        return container_scoped_w + propagates_w + from_schema_w

    @classmethod
    def from_binary_mask(cls, expression: str) -> MergePolicyFactorComb:
        """Uses binary mask expression to create combination.

        Examples:
            "111" -> container_scope=True, propagates=True, from_schema=True
            "000" -> container_scope=False, propagates=False, from_schema=False
            "110" -> container_scope=True, propagates=True, from_schema=False
        """
        if len(expression) != 3:
            raise ValueError("Expression must have length == 3.")
        return MergePolicyFactorComb(
            container_scoped="1" in expression[0],
            propagates="1" in expression[1],
            from_schema="1" in expression[2],
        )


class MergePolicyRule:
    FACTOR_WEIGHT_MAP = MergePolicyFactorWeightMap()

    def __init__(
        self,
        policy_factor_comb: MergePolicyFactorComb,
        dict_operation: BaseOperation,
        list_operation: BaseOperation,
    ):
        self.policy_factor_comb = policy_factor_comb
        self.dict_operation = dict_operation
        self.list_operation = list_operation

    def __gt__(self, o: MergePolicyRule):
        """Determines if this Rule has higher priority than the other Rule."""
        weight_map = MergePolicyRule.FACTOR_WEIGHT_MAP
        return self.policy_factor_comb.calculate_weight(
            weight_map
        ) > o.policy_factor_comb.calculate_weight(weight_map)
