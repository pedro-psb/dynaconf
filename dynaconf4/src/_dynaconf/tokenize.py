from __future__ import annotations
from _dynaconf.datastructures import DynaconfToken, PartialToken, Stack, is_token
from _dynaconf.token_registry import TokenRegistry
import re


def tokenize(
    dynaconf_string: str, token_registry: TokenRegistry
) -> DynaconfToken | None:
    if not is_token(dynaconf_string):
        return None

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
    first_token = create_token(
        partial_token_stack.pop(), None, token_registry
    )  # in evaluation order
    next_token = first_token
    while not partial_token_stack.is_empty():
        next_partial = partial_token_stack.pop()
        next_token = create_token(next_partial, next_token, token_registry)
    return next_token


def create_token(
    partial_token: PartialToken,
    next: DynaconfToken | None,
    token_registry: TokenRegistry,
) -> DynaconfToken:
    token_callback = token_registry.get_callback(partial_token.id)
    is_container_level = False
    return DynaconfToken(
        id=partial_token.id,
        args=partial_token.args or None,
        fn=token_callback.fn,
        is_lazy=token_callback.is_lazy,
        is_container_level=is_container_level,
        next=next,
    )
