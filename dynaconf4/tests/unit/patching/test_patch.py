from dynaconflib.datastructures import Patch, DataDict, PatchEngine, SchemaTree
from dynaconflib.registry import PatchOpRegistry
from dynaconflib.builtin.patch_operations import setup_patch_operations
import pytest
from dataclasses import dataclass, field
from typing import Optional

patch_registry = PatchOpRegistry("patch_operation")
setup_patch_operations(patch_registry)


@dataclass
class Scenario:
    id: str
    patches: list[Patch]
    expected: dict
    base: DataDict = field(default_factory=DataDict)
    patch_origin: Optional[dict] = None


@dataclass
class Stat:
    desc: str
    operation: str
    operation_desc: str
    base: str

    def __str__(self):
        return f"{self.desc.upper()}:base={self.base}:op={self.operation}({self.operation_desc})"


flat_empty_base = [
    Scenario(
        id=str(Stat("root-flat", "replace", "no-override-case", base="empty")),
        patch_origin={"a": 1, "b": 2},
        patches=[
            Patch("replace", ["a"], 1),
            Patch("replace", ["b"], 2),
        ],
        expected={"a": 1, "b": 2},
    ),
    Scenario(
        id=str(Stat("root-flat", "add", "override-case", base="empty")),
        patch_origin=None,  # A single dict cannot create two patches with same key and different values
        patches=[
            Patch("add", ["a"], 1),
            Patch("add", ["a"], 2),
        ],
        expected={"a": 1},
    ),
]

nested_empty_base = [
    Scenario(
        # requires each node to be build, if it doesnt exist
        id=str(Stat("dict", "add/replace", "dict-line", base="empty")),
        patch_origin={"a": {"b": {"c": 1}}},
        patches=[
            Patch("add", ["a"], dict),
            Patch("add", ["a", "b"], dict),
            Patch("replace", ["a", "b", "c"], 1),
        ],
        expected={"a": {"b": {"c": 1}}},
    ),
    Scenario(
        id=str(Stat("list", "add", "terminal-items", base="empty")),
        patches=[
            Patch("add", ["a"], list),
            Patch("add", ["a", "0"], 1),
            Patch("add", ["a", "0"], 2),
            Patch("add", ["a", "0"], 3),
        ],
        expected={"a": [3, 2, 1]},
    ),
    Scenario(
        id=str(Stat("list", "append", "terminal-items", base="empty")),
        patches=[
            Patch("add", ["a"], list),
            Patch("append", ["a", "0"], 1),
            Patch("append", ["a", "0"], 2),
            Patch("append", ["a", "0"], 3),
        ],
        expected={"a": [1, 2, 3]},
    ),
    Scenario(
        id=str(Stat("list", "add/append", "dict-inside-list", base="empty")),
        patches=[
            Patch("add", ["a"], list),
            Patch("append", ["a", "0"], dict),
            Patch("add", ["a", "0", "a"], 1),
            Patch("add", ["a", "0", "b"], 2),
            Patch("append", ["a", "0"], dict),
            Patch("add", ["a", "1", "a"], 3),
            Patch("add", ["a", "1", "b"], 4),
        ],
        expected={"a": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]},
    ),
]

populated_base = [
    Scenario(
        id=str(Stat("root-flat", "add", "override-with-existing", base="populated")),
        base=DataDict({"a": 1}),
        patches=[
            Patch("add", ["a"], 9),
            Patch("add", ["b"], 2),
        ],
        expected={"a": 1, "b": 2},
    ),
    Scenario(
        id=str(Stat("dict", "replace", "on-terminal", base="populated")),
        base=DataDict({"a": {"b": {"c": 1}}}),
        patches=[
            Patch("add", ["a"], dict),
            Patch("add", ["a", "b"], dict),
            Patch("replace", ["a", "b", "c"], 2),
        ],
        expected={"a": {"b": {"c": 2}}},
    ),
    Scenario(
        id=str(Stat("dict", "replace", "on-dict", base="populated")),
        base=DataDict({"a": {"b": {"c": 1}}}),
        patches=[
            Patch("replace", ["a"], dict),
            Patch("add", ["a", "b"], 1),
        ],
        expected={"a": {"b": 1}},
    ),
]

scenarios = flat_empty_base + nested_empty_base + populated_base


def get_ids(scenarios):
    return [f"PAT-{i:02}:{x.id}" for i, x in enumerate(scenarios)]


def patch_scenarios(scenarios):
    return [s for s in scenarios if bool(s.patch_origin)]


def get_ids_patch(scenarios):
    return [f"PAT-{i:02}:{x.id}" for i, x in enumerate(patch_scenarios(scenarios))]


@pytest.mark.parametrize("scenario", scenarios, ids=get_ids(scenarios))
def test_patch_apply(scenario: Scenario):
    schema = SchemaTree()
    patch_engine = PatchEngine(patch_registry, schema)

    base = scenario.base
    patch_engine.apply(base, scenario.patches)
    assert base == scenario.expected


@pytest.mark.parametrize(
    "scenario", patch_scenarios(scenarios), ids=get_ids_patch(scenarios)
)
def test_patch_create(scenario: Scenario):
    schema = SchemaTree()
    patch_engine = PatchEngine(patch_registry, schema)

    result = patch_engine.create(scenario.patch_origin)
    assert result == scenario.patches
