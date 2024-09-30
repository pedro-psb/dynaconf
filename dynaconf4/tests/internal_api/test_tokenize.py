from _dynaconf.create_mtree import tokenize, TokenRegistry, create_token
from _dynaconf.datastructures import DynaconfToken
from dataclasses import dataclass
import functools
import pytest
import rich


@dataclass
class Case:
    id: str
    input: str
    expected: DynaconfToken


token_registry = TokenRegistry()
int_fn = token_registry.get_callback("int").fn
str_fn = token_registry.get_callback("str").fn
sum_fn = token_registry.get_callback("sum").fn

# T = token string, e.g @foo
# A = token argument string (not split), e.g: @foo 'this is a single arg'
cases = [
    Case(
        id="[T,A]",
        input="@int 123",
        expected=DynaconfToken(id="int", args="123", lazy=False, fn=int_fn, next=None),
    ),
    Case(
        id="[T,T,A]",
        input="@str @sum 5 5 5 5",
        expected=DynaconfToken(
            id="sum",
            args="5 5 5 5",
            lazy=False,
            fn=sum_fn,
            next=DynaconfToken(
                id="str",
                args=None,
                lazy=False,
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
            lazy=False,
            fn=sum_fn,
            next=DynaconfToken(
                id="str",
                args="foobar",
                lazy=False,
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
def test_tokenizer(case):
    _create_token = functools.partial(create_token, token_registry=token_registry)
    result = tokenize(case.input, _create_token)
    debug_diff(result, case.expected)
    assert result == case.expected
