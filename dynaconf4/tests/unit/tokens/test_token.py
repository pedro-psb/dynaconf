from dynaconflib.datastructures import DynaconfToken
from dynaconflib.builtin.token_callbacks import int_fn, str_fn, sum_fn
from dataclasses import dataclass
import pytest
import rich


@dataclass
class Case:
    id: str
    input: str
    expected: DynaconfToken


# T = token string, e.g @foo
# A = token argument string (not split), e.g: @foo 'this is a single arg'
cases = [
    Case(
        id="[T,A]",
        input="@int 123",
        expected=DynaconfToken(
            id="int", args="123", is_lazy=False, fn=int_fn, next=None
        ),
    ),
    Case(
        id="[T,T,A]",
        input="@str @sum 5 5 5 5",
        expected=DynaconfToken(
            id="sum",
            args="5 5 5 5",
            is_lazy=False,
            fn=sum_fn,
            next=DynaconfToken(
                id="str",
                args=None,
                is_lazy=False,
                fn=str_fn,
                next=None,
            ),
        ),
    ),
    Case(
        id="[T,A,T,A]",
        input="@str foobar @sum 5 5 5 5",  # may not be evaluatable, but we are only tokenizing
        expected=DynaconfToken(
            id="sum",
            args="5 5 5 5",
            is_lazy=False,
            fn=sum_fn,
            next=DynaconfToken(
                id="str",
                args="foobar",
                is_lazy=False,
                fn=str_fn,
                next=None,
            ),
        ),
    ),
]


def debug_diff(result, expected):
    print("\n> Result and Expected")
    rich.print(result)
    rich.print(expected)


@pytest.mark.parametrize("case", cases)
def test_tokenizer(case, registries):
    token_registry = registries.token_callbacks
    result = DynaconfToken.create(case.input, token_registry)
    debug_diff(result, case.expected)
    assert result == case.expected
