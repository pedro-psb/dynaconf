import random
from _dynaconf.datastructures import (
    MergePolicyFactorComb,
    MergePolicyFactorWeightMap,
)


from _dynaconf.abstract import BaseMergePolicyRegistry


class MergePolicyRegistry(BaseMergePolicyRegistry):
    def __init__(self):
        self._policy_factor_weight_map = MergePolicyFactorWeightMap()

    def get_policy_factor_weight_map(self) -> MergePolicyFactorWeightMap:
        return self._policy_factor_weight_map

    def update_policy_factor_weight_map(
        self, policy_priority_definition: list[MergePolicyFactorComb]
    ):
        self._policy_factor_weight_map = create_merge_policy_weight_map(
            policy_priority_definition
        )


def create_merge_policy_weight_map(
    policy_priority_list: list[MergePolicyFactorComb],
) -> MergePolicyFactorWeightMap:
    """Calculates and creates the policy weights respecting the MergePolicyFactorComb order.

    Params:
        policy_priority_list:
            A list with the Factor combinations from high to low priority. This is the constraint
            that declares how merge behaves behave (what factor combination wins).
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
        trial_weight_map = MergePolicyFactorWeightMap((a, b), (c, d), (e, f))
        trial_results = [
            i.calculate_weight(trial_weight_map) for i in policy_priority_list
        ]
        count += 1
    return trial_weight_map


if __name__ == "__main__":
    # TODO: arrange this to reflect our default policy
    # probably want to write some scenario test cases to validate that.
    policy_priority_list = [
        MergePolicyFactorComb.from_binary_mask("000"),
        MergePolicyFactorComb.from_binary_mask("001"),
        MergePolicyFactorComb.from_binary_mask("010"),
        MergePolicyFactorComb.from_binary_mask("011"),
        MergePolicyFactorComb.from_binary_mask("100"),
        MergePolicyFactorComb.from_binary_mask("101"),
        MergePolicyFactorComb.from_binary_mask("110"),
        MergePolicyFactorComb.from_binary_mask("111"),
    ]
    map = create_merge_policy_weight_map(policy_priority_list)
    print(map)
