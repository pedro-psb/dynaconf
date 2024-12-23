from __future__ import annotations
from typing import NamedTuple


class MergePolicyRuleAttrWeightMap(NamedTuple):
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


class MergePolicyRuleAttr(NamedTuple):
    """The MergePolicy Rule attributes that influences a Rule priority resolution.

    Params:
        container_scoped: If a Rule is scoped at the container level or at the item-level.
        propagates: If a Rule should propagate or not (a one-off). For example, a Rule
            that defines that root level should merge, but that this behavior should
            not propagate to the rest of the tree.
        from_schema: If a Rule was defined in the schema (statically) or dynamically.
            For example, in a settings file with dynaconf tokens is dynamic.
    """

    container_scoped: bool
    propagates: bool
    from_schema: bool
    # TODO: add attribute 'inherited' to convey whether the rule came from the previous
    # node in the data tree.

    def calculate_weight(self, factor_weight_map: MergePolicyRuleAttrWeightMap) -> int:
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
    def from_binary_mask(cls, expression: str) -> MergePolicyRuleAttr:
        """Uses binary mask expression to create combination.

        Examples:
            "111" -> container_scope=True, propagates=True, from_schema=True
            "000" -> container_scope=False, propagates=False, from_schema=False
            "110" -> container_scope=True, propagates=True, from_schema=False
        """
        if len(expression) != 3:
            raise ValueError("Expression must have length == 3.")
        return MergePolicyRuleAttr(
            container_scoped="1" in expression[0],
            propagates="1" in expression[1],
            from_schema="1" in expression[2],
        )


class MergePolicyRule:
    """A Rule that defines which operation should be used in the items of a dict or list.

    Params:
        rule_attributes: The Rule Attributes that influences this rule weight/score.
        dict_operation: The operation that should be used in a dict if this Rule wins.
        list_operation: The operation that should be used in a list if this Rule wins.

    Class Attributes:
        FACTOR_WEIGHT_MAP: The map between Rule Attributes and weights based on their values. This
            should be shared by all `MergePolicyRule` instances.
    """

    FACTOR_WEIGHT_MAP = MergePolicyRuleAttrWeightMap()

    def __init__(
        self,
        rule_attributes: MergePolicyRuleAttr,
        dict_operation: BaseOperation,
        list_operation: BaseOperation,
    ):
        self.rule_attributes = rule_attributes
        self.dict_operation = dict_operation
        self.list_operation = list_operation

    def __gt__(self, o: MergePolicyRule):
        """Determines if this Rule has higher priority than the other Rule."""
        weight_map = MergePolicyRule.FACTOR_WEIGHT_MAP
        self_weight = self.rule_attributes.calculate_weight(weight_map)
        other_weight = o.rule_attributes.calculate_weight(weight_map)
        return self_weight > other_weight
