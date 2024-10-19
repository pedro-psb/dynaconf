from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from _dynaconf.abstract import BaseMergeTree, BaseOperation
from _dynaconf.datastructures import DynaconfToken, MergeTree, TreePath, ensure_rooted

from .token_registry import Replace, TokenRegistry
from .tokenize import tokenize


def configure_merge_policy():
    policy_priority_definition = [
        MergePolicyFactorComb(
            container_scoped=True,
            propagates=True,
            from_schema=True,
        )
    ]
    factor_weight_map = create_policy_factor_weight_map(policy_priority_definition)
    MergePolicyRule.FACTOR_WEIGHT_MAP = factor_weight_map


def create_policy_factor_weight_map(
    policy_priority_definition: list[MergePolicyFactorComb],
) -> MergePolicyFactorWeightMap:
    """Calculates and creates the policy weights respecting the MergePolicyFactors order.

    Params:
        policy_priority_definition: A list with the Factor combinations from high to low priority.
            This is the constraint definition on how the policy should behave (who wins).
    """
    return MergePolicyFactorWeightMap(
        container_scoped=(10, 10),
        propagates=(4, 4),
        from_schema=(1, 1),
    )


@dataclass
class MergePolicyFactorWeightMap:
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


@dataclass
class MergePolicyFactorComb:
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


def create_merge_tree(
    data: dict,
    mtree_cls: type[BaseMergeTree] = MergeTree,
    token_registry: TokenRegistry = TokenRegistry(),
    # merge_policy: BaseMergePolicy = MergePolicy(),
):
    """Create a MergeTree instance from a @data tree.

    The @data may contain special dynaconf tokens, such as container-level and
    terminal-level tokens.

    container-level token example: `"listy": [1,2,3, "@merge_unique"]`
    terminal-level token example: `"leafy": "@int 123"`

    Args:
        data: The data that will be used to create the merge tree from.
        mtree_cls: The MergeTree class implementation that will be used. This should
            be a subclass of BaseMergeTree.
        token_registry: The object containing the token_id:token_callback relationship.
    """
    mtree = mtree_cls()
    default_terminal_operation = Replace

    def traverse_container(
        container_path: TreePath,
        container: dict | list,
    ):
        for key, value in items(container):
            # Recursive case
            if isinstance(value, dict | list):
                traverse_container(container_path + key, value)
                continue

            # Base case: value is terminal
            token_operation = None
            if token := tokenize(value, token_registry):
                if token.is_container_level is True or token.is_lazy:
                    mtree.add_meta_token(container_path, token)
                    return
                token_operation, evaluated = evaluate(token, key)
                # return only a value and check if is a MetaValue
                # update value if it is not
                value = evaluated or value

            # priority merge resolution
            container_level_operation = first(mtree.get_meta_token(container_path))
            merge_operation = (
                token_operation
                or container_level_operation
                or default_terminal_operation
            )
            mtree.add(container_path, merge_operation(key, value))

    data = ensure_rooted(data)
    traverse_container(TreePath(("root",)), data["root"])
    return mtree


def first(sequence):
    """Returns the first element of a sequence or None."""
    if sequence:
        return sequence[0]
    return None


def evaluate(
    token: DynaconfToken, key: str | int
) -> tuple[type[BaseOperation] | None, Any]:
    """Evaluate DynaconfToken.

    Returns a tuple of (merge_operation, value)
    """
    next_token: DynaconfToken | None = token
    value = None
    merge_operation = None
    while next_token:
        if isinstance(next_token.fn, type) and issubclass(next_token.fn, BaseOperation):
            if next_token.next:
                raise ValueError(
                    f"BaseOperation should be the left-most token: {
                        next_token.fn!r}"
                )
            merge_operation = next_token.fn
            break
        value = next_token.fn(
            next_token.args, cumulative=value
        )  # TODO: add proper types to those callables
        next_token = next_token.next
    return merge_operation, value


def items(container):
    if isinstance(container, dict):
        return container.items()
    elif isinstance(container, list):
        return enumerate(container)
    else:
        raise RuntimeError(f"Must be a dict or list: {container}")
