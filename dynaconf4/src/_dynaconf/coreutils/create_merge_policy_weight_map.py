from _dynaconf.datastructures import (
    MergePolicyFactorComb,
    MergePolicyFactorWeightMap,
)


def create_merge_policy_weight_map(
    policy_priority_definition: list[MergePolicyFactorComb],
) -> MergePolicyFactorWeightMap:
    """Calculates and creates the policy weights respecting the MergePolicyFactorComb order.

    Params:
        policy_priority_definition:
            A list with the Factor combinations from high to low priority. This is the constraint
            that declares how merge behaves behave (what factor combination wins).
    """
    # TODO: implement this with the variable randomizer
    return MergePolicyFactorWeightMap(
        container_scoped=(10, 10),
        propagates=(4, 4),
        from_schema=(1, 1),
    )
