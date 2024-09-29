from dataclasses import dataclass

import pytest

from internal_api.apply_mtree import apply_merge_tree
from internal_api.create_mtree import create_merge_tree
from internal_api.registry import (
    Add,
    Append,
    AppendUnique,
    JumpMerge,
    Merge,
    Replace,
)
from internal_api.datastructures import MergeTree


@dataclass
class DataProfile:
    max_deph: int
    max_width: int
    container_nodes_count: int
    terminal_nodes_count: int


@dataclass
class Scenario:
    """Parse/merge test scenario.

    This data can be used partially by functions, so we can test intermediate data states.
    For example, here we break 'merge' feature in two steps, so the second doesnt depend on the
    correctness of the first:

    A) create_merge_tree(data=scenario.raw) -> MergeTree
    B) apply_merge_tree(base=scenario.base, scenario.merge_tree)

    Params:
        id: Name identifier for this scenario.
        base: The base data where data will be merged.
        expected: The expected state of base after the merge.
        merge_tree: The MergeTree implementation to use. Other implementations can be
            tested by adding extra repr of them and parametrizing with the scenario input.
    """

    id: str

    # data input
    income: dict
    base: dict
    expected: dict
    # implementation
    merge_tree: MergeTree
    # docs (explaining the test case)
    docs: str = ""

    def data_profile(self):
        return DataProfile(self.base)


scenario_set = [
    Scenario(
        id="simple",
        docs="""\
        general:
            Replace and Add meaning is strict, so we have no ambiguity on what is happening.
            Nevetheless, our default behavior is probably "Add or Replace".

        create_merge_tree(@income) -> @merge_tree
            Even though @add is no-op when the key exists in base, it should appear in the
            MergeTree, because that is a declarative data structure. If the user (or us) overrides
            the token-callback for @add, it may do something different.

        apply_merge_tree(@base, @merge_tree) -> @expected
            - The default behavior for Terminal values is replacing in @base on collision*.
            - As 'key_b' collides, @income:'root.key_b' should replace @base.'root.value_b'.
            - As 'key_a' collides and @add doesn't replace on collision, it is a no-op""",
        income={
            "key_a": "@add @int 999",
            "key_b": 999,
        },
        base={
            "root": {"key_a": 111, "key_b": 222, "key_c": 111},
        },
        merge_tree=MergeTree(
            {
                "root": [
                    Add("key_a", 999),  # no-op
                    Replace("key_b", 999),
                ]
            }
        ),
        expected={"root": {"key_a": 111, "key_b": 999, "key_c": 111}},
    ),
    Scenario(
        id="simple nesting with mergin",
        income={
            "value_c": "@add @int 999",
            "nested": {"bar": "@int 999", "spam": "@int 555"},
        },
        base={
            "root": {
                "value_a": 111,
                "nested": {
                    "foo": 333,
                    "bar": 444,
                },
            },
        },
        expected={
            "root": {
                "value_a": 111,
                "nested": {"foo": 333, "bar": 999, "spam": 555},
                "value_c": 999,
            }
        },
        merge_tree=MergeTree(
            {
                "root": [
                    Add("value_c", 999),
                    Merge("nested", None),
                ],
                "root.nested": [
                    Add("spam", 555),
                    Replace("bar", 999),
                ],
            }
        ),
    ),
    Scenario(
        id="simple nesting replacing",
        income={},
        base={
            "root": {
                "value_a": 111,
                "nested": {
                    "foo": 333,
                    "bar": 444,
                },
            },
        },
        expected={
            "root": {"value_a": 111, "nested": {"something": "else"}, "value_c": 999}
        },
        merge_tree=MergeTree(
            {
                "root": [
                    Add("value_c", 999),
                    Replace("nested", {"something": "else"}),
                ],
            }
        ),
    ),
    Scenario(
        id="simple nesting replacing",
        income={},
        base={
            "root": {
                "listy": [1, 2, 3],
            },
        },
        expected={"root": {"listy": [1, 2, 3, "appended", 4]}},
        merge_tree=MergeTree(
            {
                "root": [
                    Merge("listy", None),
                ],
                "root.listy": [
                    Add(0, 999),
                    Append(None, "appended"),
                    AppendUnique(None, 2),
                    AppendUnique(None, 3),
                    AppendUnique(None, 4),  # only this will be appended
                ],
            }
        ),
    ),
    Scenario(
        id="list nesting whith merging",
        income={},
        base={
            "root": {
                "listy": [{"foo": "bar"}, 2, 3],
            },
        },
        expected={
            "root": {
                "listy": [{"foo": False, "new": 54321}, 2, 3, {"foo": "different"}]
            }
        },
        merge_tree=MergeTree(
            {
                "root": [
                    Merge("listy", None),
                ],
                "root.listy": [
                    AppendUnique(None, {"foo": "bar"}),
                    AppendUnique(None, {"foo": "different"}),
                    Merge(0, None),
                ],
                "root.listy.0": [Replace("foo", False), Add("new", 54321)],
            }
        ),
    ),
    Scenario(
        id="jump for optimizing long merge chains",
        income={},
        base={
            "root": {"level-1": [{"level-2": {"level-3": {"foo": 111}}}]},
        },
        expected={
            "root": {"level-1": [{"level-2": {"level-3": {"foo": 999, "new": 54321}}}]}
        },
        merge_tree=MergeTree(
            {
                "root": [  # TODO: allow syntax like '@index 1 or @index -1'
                    JumpMerge("level-1.0.level-2.level-3", None),
                ],
                "root.level-1.0.level-2.level-3": [
                    Replace("foo", 999),
                    Add("new", 54321),
                ],
            }
        ),
    ),
]


def debug_diff(result, expected, raw):
    from internal_api.utils import section_print
    section_print("raw", raw)
    section_print("result", result)
    section_print("expected", expected)


@pytest.mark.parametrize("scenario", scenario_set)
def test_apply_merge_tree(scenario: Scenario):
    result = apply_merge_tree(scenario.base, scenario.merge_tree)
    debug_diff(result, scenario.expected, scenario.base)
    assert result == scenario.expected


@pytest.mark.parametrize("scenario", scenario_set)
def test_create_merge_tree(scenario: Scenario):
    result_mtree = create_merge_tree(scenario.income, MergeTree)
    debug_diff(result_mtree, scenario.merge_tree, scenario.income)
    assert result_mtree == scenario.merge_tree
