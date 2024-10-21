import random
from _dynaconf.datastructures import (
    MergePolicyRuleAttr,
    MergePolicyRuleAttrWeightMap,
)


from _dynaconf.abstract import BaseMergePolicyRegistry


class MergePolicyRegistry(BaseMergePolicyRegistry):
    def __init__(self):
        self._policy_factor_weight_map = MergePolicyRuleAttrWeightMap()

    def get_policy_factor_weight_map(self) -> MergePolicyRuleAttrWeightMap:
        return self._policy_factor_weight_map

    def update_policy_factor_weight_map(
        self, policy_priority_definition: list[MergePolicyRuleAttr]
    ):
        self._policy_factor_weight_map = create_merge_policy_weight_map(
            policy_priority_definition
        )


def create_merge_policy_weight_map(
    rule_attribute_priority_list: list[MergePolicyRuleAttr],
) -> MergePolicyRuleAttrWeightMap:
    """Calculates and creates the policy weights respecting the MergePolicyRuleAttr order.

    Params:
        rule_attribute_priority_list:
            A list with the Rule Attributes ordered from high to low priority on Rule resolution.
            This is the constraint that declares how merge behaves behave (what Rule Attribute wins).
    """
    trial_results = [0, 1]
    limit = 1000
    count = 0
    while trial_results != sorted(trial_results, reverse=True):
        if count > limit:
            raise RuntimeError(
                "Calculation taking too long. Those constraint are probably hard to solve."
            )
        a, b, c, d, e, f = [random.randint(1, 100) for _ in range(6)]
        trial_weight_map = MergePolicyRuleAttrWeightMap((a, b), (c, d), (e, f))
        trial_results = [
            i.calculate_weight(trial_weight_map) for i in rule_attribute_priority_list
        ]
        count += 1
    return trial_weight_map


if __name__ == "__main__":
    # TODO: arrange this to reflect our default policy
    # probably want to write some scenario test cases to validate that.
    rule_attribute_priority_list = [
        MergePolicyRuleAttr.from_binary_mask("000"),
        MergePolicyRuleAttr.from_binary_mask("001"),
        MergePolicyRuleAttr.from_binary_mask("010"),
        MergePolicyRuleAttr.from_binary_mask("011"),
        MergePolicyRuleAttr.from_binary_mask("100"),
        MergePolicyRuleAttr.from_binary_mask("101"),
        MergePolicyRuleAttr.from_binary_mask("110"),
        MergePolicyRuleAttr.from_binary_mask("111"),
    ]
    map = create_merge_policy_weight_map(rule_attribute_priority_list)
    print(map)
