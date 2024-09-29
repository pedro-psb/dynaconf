from __future__ import annotations
from typing import Callable
from internal_api.datastructures import DynaconfToken, PartialToken, Stack, is_token
from internal_api.registry import TokenRegistry
import re


def tokenize(dynaconf_string: str, create_token: Callable) -> DynaconfToken:

    def split_string(s):
        pattern = r"(@[a-zA-Z0-9_-]+)"
        result = re.split(pattern, s)
        return [x.strip() for x in result if x]

    # 1. Create partial token with information we have right now.
    # The split_string has the form (T[, A], T[, A], ...), where
    # * T is a token identifier, e.g: "@insert"
    # * A is a string of arguments, e.g "0 foobar"
    s = split_string(dynaconf_string)
    s.reverse()
    partial_token_stack = Stack[PartialToken]()
    args_memory = None
    for item in s:
        if is_token(item):
            partial_token_stack.push(PartialToken(item[1:], args_memory))
            args_memory = None
        else:
            args_memory = item

    # 2. Create the final token
    # Now we need to use external context and chain each token with the next
    # partial_token_stack.reverse()
    first_token = create_token(partial_token_stack.pop(), None)  # in evaluation order
    next_token = first_token
    while not partial_token_stack.is_empty():
        next_partial = partial_token_stack.pop()
        next_token = create_token(next_partial, next_token)
    return next_token


def create_token(
    partial_token: PartialToken,
    next: DynaconfToken | None,
    token_registry: TokenRegistry,
) -> DynaconfToken:
    token_callback = token_registry.get_callback(partial_token.id)
    is_meta_token = False
    return DynaconfToken(
        id=partial_token.id,
        args=partial_token.args or None,
        lazy=token_callback.lazy,
        fn=token_callback.fn,
        meta=is_meta_token,
        next=next,
    )
