from __future__ import annotations
from typing import NamedTuple, Optional, Callable, TYPE_CHECKING
from .linear import Stack
import re

if TYPE_CHECKING:
    from dynaconflib.registry import TokenRegistry


class DynaconfToken(NamedTuple):
    id: str
    args: Optional[str]
    is_lazy: bool
    fn: Callable
    next: Optional[DynaconfToken]
    is_container_level: bool = False

    @classmethod
    def create(cls, input: str, token_registry: TokenRegistry) -> DynaconfToken | None:
        """Create a DynaconfToken using TokenCallbacks from TokenRegistry."""
        if not DynaconfToken.is_token(input):
            return None

        # 1. Create partial token with information we have right now.
        # The split_string has the form (T[, A], T[, A], ...), where
        # * T is a token identifier, e.g: "@insert"
        # * A is a string of arguments, e.g "0 foobar"
        s = DynaconfToken.split_string(input)
        s.reverse()
        partial_token_stack = Stack[PartialToken]()
        args_memory = None
        for item in s:
            if DynaconfToken.is_token(item):
                partial_token_stack.push(PartialToken(item[1:], args_memory))
                args_memory = None
            else:
                args_memory = item

        # 2. Create the final token
        # * Get correct TokenCallback for each identifier
        # * Chain each token with the next in partial_token_stack
        first_token = DynaconfToken.assemble_token(
            partial_token_stack.pop(), None, token_registry
        )
        next_token = first_token
        while not partial_token_stack.is_empty():
            next_partial = partial_token_stack.pop()
            next_token = DynaconfToken.assemble_token(
                next_partial, next_token, token_registry
            )
        return next_token

    @staticmethod
    def is_token(value: str) -> bool:
        if not isinstance(value, str):
            return False
        return isinstance(value, str) and value.startswith("@")

    @staticmethod
    def split_string(s):
        pattern = r"(@[a-zA-Z0-9_-]+)"
        result = re.split(pattern, s)
        return [x.strip() for x in result if x]

    @staticmethod
    def assemble_token(
        partial_token: PartialToken,
        next: DynaconfToken | None,
        token_registry: TokenRegistry,
    ) -> DynaconfToken:
        token_callback = token_registry.get(partial_token.id)
        is_container_level = False
        return DynaconfToken(
            id=partial_token.id,
            args=partial_token.args or None,
            fn=token_callback.fn,
            is_lazy=token_callback.is_lazy,
            is_container_level=is_container_level,
            next=next,
        )


class PartialToken(NamedTuple):
    id: str
    args: Optional[str]


class TokenCallback(NamedTuple):
    fn: Callable
    is_lazy: bool = False
    is_merge_operation: bool = False
