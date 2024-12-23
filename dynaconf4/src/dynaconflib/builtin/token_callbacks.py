from __future__ import annotations
from typing import TYPE_CHECKING
from dynaconflib.datastructures import TokenCallback

if TYPE_CHECKING:
    from dynaconflib.registry import TokenRegistry


def setup_tokens(regsitry: TokenRegistry):
    regsitry.add("int", TokenCallback(int_fn))
    regsitry.add("str", TokenCallback(str_fn))
    regsitry.add("sum", TokenCallback(sum_fn))


def int_fn(o, *args, **kwargs):
    return int(o)


def str_fn(o, *args, **kwargs):
    return str(o)


def sum_fn(o, *args, **kwargs):
    return sum(o)
