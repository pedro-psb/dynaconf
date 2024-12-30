from dynaconflib.entrypoint import Dynaconf
from dataclasses import dataclass, field
from typing import Any

import pytest


@dataclass
class Scenario:
    id: str
    expected: dict
    args: list = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)
    setitem_calls: list[tuple[str], Any] = field(default_factory=list)
    environ: dict = field(default_factory=dict)


def get_ids(scenarios):
    return [f"ENT-{i:02}:{x.id}" for i, x in enumerate(scenarios)]


def Kw(**kwargs):
    return kwargs


def Id(*args):
    return ":".join(args)


def Call(*key_path: str, value: Any):
    return key_path, value


basic = [
    Scenario(id=Id("sanity-check"), expected={}),
    Scenario(
        id=Id("simple-data"),
        kwargs=Kw(data={"a": 1, "b": 2}),
        expected={"a": 1, "b": 2},
    ),
    Scenario(
        id=Id("simple-setitem-calls"),
        kwargs=Kw(data={"a": 1, "b": 2}),
        setitem_calls=[Call("c", value=3)],
        expected={"a": 1, "b": 2, "c": 3},
    ),
    Scenario(
        id=Id("simple-environ"),
        environ={"DYNACONF_A": "foo", "DYNACONF_B": "bar"},
        expected={"a": "foo", "b": "bar"},
    ),
]

scenarios = basic


@pytest.mark.parametrize("scenario", scenarios, ids=get_ids(scenarios))
def test_entrypoint_noschema(scenario: Scenario, monkeypatch):
    """
    GIVEN a set of Args and Kwargs
    AND a set of setitem Calls pattern
    AND a mocked environ data set

    WHEN the dynaconf instance is instantiated with them
    AND the set settiem Call pattern are applied

    THEN settings will have the expected value
    AND the internal active namespace will match the frontend namespace
    """
    # GIVEN
    args = scenario.args
    kwargs = scenario.kwargs
    setitem_calls = scenario.setitem_calls
    expected = scenario.expected
    for k, v in scenario.environ.items():
        monkeypatch.setenv(k, v)

    # WHEN
    settings = Dynaconf(*args, **kwargs)
    for call_args in setitem_calls:
        key_path, value = call_args
        settings[key_path[0]] = value

    # THEN
    core = settings.__get_dynaconf__()
    current_ns = core.namespaces.get_current()
    assert settings == expected
    assert current_ns.data == settings
